# /usr/bin/env python3
"""
MDR version with a preprocessing that splits the input file into chunks
that saves back to storage for workers to read.
"""

import argparse
import gzip
import json
import logging
import math
import os
import pathlib
import pickle
import timeit
import time
from itertools import combinations_with_replacement, product

import lithops
import numpy as np
import yaml
from dataplug.fileobject import CloudObject
from dataplug.formats.genomics.vcf import VCF, partition_num_chunks
# from custom_vcf import VCF, partition_num_chunks
from dataplug.util import setup_logging


def parse_labels(labels_data):
    """Parse labels from input string and keep only cases/controls"""
    labels = list()
    line_count = 0
    for row in labels_data.splitlines():
        if line_count == 0 or line_count == 1:  # FIXME: always skip first two lines?
            line_count += 1
        else:
            r = row.strip(" ")
            labels.append(int(r[len(r) - 1]))  # FIXME: only last digit?
            line_count += 1
    return labels


def filter_imputation(x):
    """Definition of the filter for imputation. We believe the value only if > 0.9"""
    if float(x) > 0.9:
        return 1
    return 0


# Vectorize function
input_filter = np.vectorize(filter_imputation)


def get_keyval(x: str):
    """Transform to key + values"""
    aux = x.split()
    key = aux[0] + "-" + aux[1] + "-" + aux[2]
    val = input_filter(aux[5:])
    return (key, val)


def parse_sample(samples_data):
    """Parse sample information (str) into a dict"""
    sample = dict()
    # with gzip.open(samplepath,'rt') as fin:
    # fin = gzip.decompress(samplepath)
    # content = samples_data.decode("utf-8")
    for line in samples_data.splitlines():
        if line.startswith("BCFv"):
            continue
        if line.startswith("#"):
            continue
        key, val = get_keyval(line)
        sample[key] = val
    return sample


def save_output(storage, bucket, output_key, mdr_error):
    """Save mdr_error to output directory, compressed"""
    output_buffer = []
    for pair in mdr_error:
        result = list(pair[0]) + pair[1]
        result = [str(x).replace("'", "") for x in result] + ["\n"]
        output_buffer.append(" ".join(result))
    output_data = "".join(output_buffer)
    compressed_data = gzip.compress(output_data.encode("utf-8"))
    storage.put_object(Bucket=bucket, Key=output_key, Body=compressed_data)


def transform_patients(x):
    """Apply function to every SNP-SNP row to get the interaction matrix"""
    # 1 - Transform to numpy arrays NO HBASE
    patients1 = np.array(x[0])
    patients2 = np.array(x[1])

    # 2 - Reshape as 3 x n patients
    patientsdf1 = np.reshape(patients1, (int(len(patients1) / 3), 3))
    patientsdf2 = np.reshape(patients2, (int(len(patients2) / 3), 3))

    # 3 - Transform to integer
    pt1 = np.matmul(patientsdf1, np.transpose([1, 2, 3])) * 3
    pt2 = np.matmul(patientsdf2, np.transpose([0, 1, 2]))
    ptcode = pt1 - pt2

    return ptcode


def count_occurrences(data):
    """Transform the counts to an array"""
    unique, counts = np.unique(data, return_counts=True)
    dtcounts = dict(zip(unique, counts))

    aux = list()
    for i in range(10):
        if i in dtcounts:
            aux.append(dtcounts[i])
        else:
            aux.append(0)

    return np.array(aux)


def apply_risk(patients, risk):
    """Apply risk vector to classify the patients"""
    prediction = np.zeros(len(patients))
    casevalues = np.where(risk == 1)

    for n in casevalues[0][1:]:
        prediction[patients == n] = 1

    return prediction.astype(int)


def get_risk_array(
    patients,
    cv_sets,
    trainset,
    testset,
    npcases,
    npcontrols,
    ccratio,
):
    """
    Count number of cases and number of controls for each column and return the high risk combinations.
    Then, use the high risk predictor to obtain the classification and prediction error.
    """
    # Error list
    # trainerror = list()
    testerror = list()

    for i in range(cv_sets):
        # 1 - Get the sets for the iteration
        traindata = trainset[i]
        testdata = testset[i]
        # Ntrain = np.sum(traindata)
        Ntest = np.sum(testdata)

        # 2 - Sum only the cases from training set
        cases = patients * npcases.T * traindata.T
        sumcases = count_occurrences(cases)

        # 2 - Sum only the controls
        controls = patients * npcontrols.T * traindata.T
        sumcontrols = count_occurrences(controls)

        # 3 - Get risk array
        # risk = sumcases/sumcontrols
        risk = np.divide(
            sumcases,
            sumcontrols,
            out=np.zeros(sumcases.shape, dtype=float),
            where=sumcontrols != 0,
        )
        # risk[np.isnan(risk)] = 0

        # 4 - Transform to high risk = 1, low risk = 0
        risk[risk >= ccratio] = 1
        risk[risk < ccratio] = 0

        # 5 - Classify training set
        prediction = apply_risk(patients, risk)

        # Get classification error
        # trainerror.append((((npcases.T[0] == prediction)*traindata.T)[0]).sum()/Ntrain)

        # 6 - Get classification error
        cv_testerror = (prediction + npcases.T[0]) % 2
        cv_testerror = (1 - cv_testerror) * testdata.T
        testerror.append((cv_testerror.sum() / Ntest))

    return testerror


def apply_mdr_dict(
    x,
    rd1,
    rd2,
    cv_sets,
    trainset,
    testset,
    npcases,
    npcontrols,
    ccratio,
):
    """Apply MDR to every SNP-SNP combination reading from a dict"""
    key1 = x[0]
    key2 = x[1]
    row1 = rd1[key1]
    row2 = rd2[key2]

    patients = transform_patients((row1, row2))
    testerror = get_risk_array(
        patients,
        cv_sets,
        trainset,
        testset,
        npcases,
        npcontrols,
        ccratio,
    )
    return (x[0], x[1]), testerror


def process_files(
    input_file: str,
    # worker_id: int,
    # pairs_of_slices: List[Tuple[CloudObjectSlice, CloudObjectSlice]],
    # mdr_config: Dict,
):
    """Processes a list of pairs of slices of a VCF file.

    Main lithops worker/function code.
    """

    # timer_00 = timeit.default_timer()
    timer_00 = time.time()
    worker_id, num_chunks, paired_slice_keys, mdr_config = pickle.load(open(input_file, "rb"))

    co = CloudObject.from_bucket_key(
        VCF,
        mdr_config["bucket"],
        mdr_config["samples_key"],
    )
    # data_slices = co.partition(partition_num_chunks, num_chunks=num_chunks)
    # paired_slices = list(combinations_with_replacement(data_slices, 2))
    # start, end = chunk_ranges
    # pairs_of_slices = paired_slices[start:end]

    # timer_01 = timeit.default_timer()
    timer_01 = time.time()

    print(f"Worker {worker_id} processing {len(paired_slice_keys)} pairs of data slices (chunks)...")
    # for one, other in pairs_of_slices:
    #     print(f"Worker {worker_id} -> {one.chunk_id}-{other.chunk_id}")

    # Get storage client from cloud object
    storage = co.storage

    # Read patients information from storage
    res = storage.get_object(Bucket=mdr_config["bucket"], Key=mdr_config["patients_key"])
    labels = parse_labels(res["Body"].read().decode("utf-8"))

    # Get np array with cases == 1
    npcases = np.array(labels)

    # Get np array with controls == 1
    npcontrols = np.where((npcases == 0) | (npcases == 1), npcases ^ 1, npcases)

    # Get cases/controls ratio. We will use the number as the high risk/low risk separator
    ccratio = npcases.sum(axis=0) / npcontrols.sum(axis=0)
    print(f"Ratio of cases/controls is {ccratio}")

    # print('Creating CV sets...')
    # Create training and test set
    n_patients = len(labels)
    # TODO: check that number of patients corresponds with number of samples
    if "n_patients" in mdr_config:
        assert n_patients == mdr_config["n_patients"]
    # Ntrain = Npatients / 5 * 4
    # Ntest = Npatients / 5

    # Create training and test set for a 5-CV
    block_size = n_patients / mdr_config["CV_sets"]
    trainset = list()
    testset = list()

    # Create two list with the train and test indexes
    for i in range(mdr_config["CV_sets"]):
        nptrain = np.array([np.ones(n_patients, dtype=int)]).T
        nptrain[int(i * block_size): int(i * block_size + block_size)] = 0
        nptest = np.where((nptrain == 0) | (nptrain == 1), nptrain ^ 1, nptrain)

        trainset.append(nptrain)
        testset.append(nptest)

    # timer_02 = timeit.default_timer()
    timer_02 = time.time()

    all_pairs = 0
    all_candidates = 0
    time_breakdown = []

    for one_slice_key, other_slice_key in paired_slice_keys:
        # timer_1 = timeit.default_timer()
        timer_1 = time.time()

        one_slice_id = pathlib.Path(one_slice_key).name.split(".", 1)[0]
        other_slice_id = pathlib.Path(other_slice_key).name.split(".", 1)[0]

        # one_slice = data_slices[one_slice_id]
        # other_slice = data_slices[other_slice_id]
        # one_slice_key = slice_keys[one_slice_id]
        # other_slice_key = slice_keys[other_slice_id]
        print(f"    > Worker {worker_id} > Loading data slices {one_slice_id} and {other_slice_id}.")

        # Read samples files
        # FIXME: do not download the same slice twice
        # sample_1 = parse_sample(one_slice.get())
        res = storage.get_object(Bucket=mdr_config["bucket"], Key=one_slice_key)
        sample_1 = parse_sample(res["Body"].read().decode("utf-8"))
        # sample_2 = parse_sample(other_slice.get())
        res = storage.get_object(Bucket=mdr_config["bucket"], Key=other_slice_key)
        sample_2 = parse_sample(res["Body"].read().decode("utf-8"))
        # timer_2 = timeit.default_timer()
        timer_2 = time.time()

        # Keep only the keys information
        sample_1_ids = list(sample_1.keys())
        sample_2_ids = list(sample_2.keys())

        # Get all the combinations
        cartesiankeys = product(sample_1_ids, sample_2_ids)
        # FIXME: this matches all with all with repetitions:
        # A -> B is different than B -> A (both cases are analyzed)
        # Is this correct?  Files/slices are only matched without repetitions
        # This happens when matching the slice with itself

        # Compute MDR
        print(f"    > Worker {worker_id} > Applying MDR...")
        mdr_error = list()
        cv_sets = mdr_config["CV_sets"]
        prediction_power_tol = float(mdr_config["prediction_power_tol"])
        total_pairs = 0
        candidate_pairs = 0
        for x in cartesiankeys:
            # print(f"MDR on pair {x}")
            total_pairs += 1
            MDR_results = apply_mdr_dict(
                x,
                sample_1,
                sample_2,
                cv_sets,
                trainset,
                testset,
                npcases,
                npcontrols,
                ccratio,
            )
            cumulative_error = sum(MDR_results[1])
            # Check if SNPij is candidate to be saved
            if cumulative_error > prediction_power_tol:
                continue
            mdr_error.append(MDR_results)
            candidate_pairs += 1

        # timer_3 = timeit.default_timer()
        timer_3 = time.time()
        # Save results to file
        if len(mdr_error) > 0:
            output_path = f"{mdr_config['output_key']}/{one_slice_id}-{other_slice_id}.vcf.gz"
            save_output(storage, mdr_config["bucket"], output_path, mdr_error)

        # timer_4 = timeit.default_timer()
        timer_4 = time.time()
        print(
            f"    > MDR applied to {total_pairs} pairs by worker {worker_id}.",
            f"    > Saving {candidate_pairs} MDRERROR to file {output_path}."
            if len(mdr_error) > 0
            else "    > No candidate pairs found. Skipping output file.",
            f"    > {one_slice_id} and {other_slice_id} combined in {timer_4 - timer_1}.",
            f"    > COMBS/SEC/CORE: {total_pairs / (timer_4 - timer_1)}",
            "    >",
            sep=os.linesep,
        )
        all_pairs += total_pairs
        all_candidates += candidate_pairs
        # pair init -> read slices -> MDR -> save output
        time_breakdown.append([timer_1, timer_2, timer_3, timer_4])

    # timer_03 = timeit.default_timer()
    timer_03 = time.time()
    total_time = timer_03 - timer_00
    return {
        "total_time": total_time,
        "total_pairs": all_pairs,
        "candidate_pairs": all_candidates,
        "worker_times": [
            timer_00,  # start
            timer_01,  # load inputs + slice partitioning
            timer_02,  # parse labels
            timer_03,  # all MDR chunk pairs
        ],
        "mdr_breakdown": time_breakdown,
    }


def compute_chunk_ranges(n_tasks, n_workers):
    """Compute ranges (list indexes) to split n_tasks into n_workers."""
    chunk_size = math.ceil(n_tasks / n_workers)
    chunk_ranges = []
    start = 0

    for _ in range(n_workers):
        end = min(start + chunk_size, n_tasks)
        chunk_ranges.append((start, end))
        start = end
        if start >= n_tasks:
            break
    return chunk_ranges


def compute_chunk_ranges_balanced(n_tasks, n_workers):
    """Compute ranges (list indexes) to split n_tasks into n_workers.

    Balanced.
    Adapted from https://more-itertools.readthedocs.io/en/latest/_modules/more_itertools/more.html#divide
    """

    q, r = divmod(n_tasks, n_workers)

    chunk_ranges = []
    stop = 0
    for i in range(1, n_workers + 1):
        start = stop
        stop += q + 1 if i <= r else q
        chunk_ranges.append((start, stop))

    return chunk_ranges


def compute_combinations(workers, num_chunks, mdr_config):
    """ "Main driver code."""
    # timer_start = timeit.default_timer()
    timer_start = time.time()
    # co = CloudObject.from_s3(
    #     VCF,
    #     f"s3://{mdr_config['bucket']}/{mdr_config['samples_key']}",
    #     s3_config=minio,
    # )
    co = CloudObject.from_bucket_key(
        VCF,
        mdr_config["bucket"],
        mdr_config["samples_key"],
    )
    # Preprocessing only once per file
    parallel_config = {"verbose": 10}
    co.preprocess(parallel_config=parallel_config, debug=True, force=True)
    print(co)

    # Make and upload partitions
    data_slices = co.partition(partition_num_chunks, num_chunks=num_chunks)[
        mdr_config["chunk_start"]: mdr_config["chunk_end"]
    ]
    slice_keys = []
    for slice in data_slices:
        storage = slice.cloud_object.storage
        key = f"{mdr_config['samples_key']}_parts{num_chunks}/{slice.chunk_id}.vcf"
        storage.put_object(Body=slice.get().encode("utf-8"), Bucket=mdr_config["bucket"], Key=key)
        slice_keys.append(key)

    # slice_ids = list(range(0, num_chunks))[
    #     mdr_config["chunk_start"] : mdr_config["chunk_end"]
    # ]
    paired_slice_keys = list(combinations_with_replacement(slice_keys, 2))

    print(f"Will check {len(paired_slice_keys)} file slice combinations/pairs...")
    # for num, (one, other) in enumerate(paired_slices):
    #     print(f"    > Pair {num} > Slices {one.chunk_id}-{other.chunk_id}")

    chunk_ranges = compute_chunk_ranges_balanced(len(paired_slice_keys), workers)
    iterdata = []
    for id, (start, end) in enumerate(chunk_ranges):
        print(f"Worker {id} > Pairs {start}-{end}")
        input_file = f"{mdr_config['bucket']}/inputs/{id}.pickle"
        worker_pairs = paired_slice_keys[start:end]
        worker_input = (id, num_chunks, worker_pairs, mdr_config)
        pickle.dump(worker_input, open(input_file, "wb"), -1)
        iterdata.append(input_file)

    # timer_preprocess = timeit.default_timer()
    timer_preprocess = time.time()
    print("Running workers...")
    fexec = lithops.FunctionExecutor(runtime_memory=1024, runtime_timeout=43200)
    futures = fexec.map(process_files, iterdata)
    results = fexec.get_result(futures, throw_except=False, threadpool_size=112)

    # results = []
    # for id, (start, end) in enumerate(chunk_ranges):
    #     # Run workers locally, sequentially, instead of lithops.map + wait
    #     worker_pairs = paired_slices[start:end]
    #     for one, other in worker_pairs:
    #         print(f"Worker {id} -> {one.chunk_id}-{other.chunk_id}")
    #     result = process_files(id, worker_pairs, mdr_config)
    #     results.append(result)

    # timer_end = timeit.default_timer()
    timer_end = time.time()
    total_time = timer_end - timer_start

    times = []
    pairs = []
    candidates = []
    for result in results:
        if result is not None:
            times.append(result["total_time"])
            pairs.append(result["total_pairs"])
            candidates.append(result["candidate_pairs"])

    total_pairs = sum(pairs)
    total_candidates = sum(candidates)

    if times:
        print(f"MDR-function times. Max: {max(times)}")  # to take the worst-case
        # print(times)
        print(f"MDR applied to a total of {total_pairs} pairs")
        print(f"Found a total of {total_candidates} candidate pairs")
        print(f"Total COMBS/SEC: {total_pairs / total_time}")
        print(f"Total COMBS/SEC/CORE: {total_pairs / total_time / workers}")
    else:
        print("MDR functions failed. No results.")

    dataset_name = mdr_config["samples_key"].split("/", 1)[0]
    execution_name = f"{dataset_name}-{workers}-{num_chunks}[{mdr_config['chunk_start']}-{mdr_config['chunk_end']}]-{fexec.executor_id}"
    worker_stats = [f.stats for f in futures if not f.error]

    plots = pathlib.Path(mdr_config["plots"])
    plots.mkdir(parents=True, exist_ok=True)
    json.dump(
        worker_stats,
        open(
            f"{plots}/{execution_name}-stats.json",
            "w",
        ),
    )

    job_results = {
        "worker_results": results,
        "job_results": {
            "num_workers": workers,
            "num_chunks": num_chunks,
            "start_tstmp": timer_start,
            "preproc_tstmp": timer_preprocess,
            "end_tstmp": timer_end,
            "total_time": total_time,
            "total_pairs": total_pairs,
            "total_candidates": total_candidates,
            "score": total_pairs / total_time,
            "core_store": total_pairs / total_time / workers,
            "mdr_config": mdr_config,
        },
    }

    json.dump(
        job_results,
        open(
            f"{plots}/{execution_name}-results.json",
            "w",
        ),
    )

    print(f"Plotting the execution... {execution_name}")
    fexec.plot(dst=f"{plots}/{execution_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MDR compute.")
    parser.add_argument("config_file", type=str, help="Path to the YAML config file")
    parser.add_argument("-w", "--nworkers", type=int, help="Number of workers")
    parser.add_argument("-c", "--nchunks", type=int, help="Number of partitions of the samples file to make")
    parser.add_argument(
        "-s",
        "--start",
        type=int,
        help="To limit number of chunks to process. This marks the first one to consider.",
        default=0,
        required=False,
    )
    parser.add_argument(
        "-e",
        "--end",
        type=int,
        help="To limit number of chunks to process. This marks the end (exclusive). (Empty means 'to the last one')",
        default=None,
        required=False,
    )
    parser.add_argument(
        "-p",
        "--plots",
        type=str,
        help="Directory for plots. Created if it does not exist.",
        default="plots",
        required=False,
    )

    args = parser.parse_args()
    config_file = args.config_file
    workers = args.nworkers
    nchunks = args.nchunks
    chunk_start = args.start
    chunk_end = args.end
    plots_dir = args.plots

    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    # Dataplug setup
    setup_logging(logging.INFO)
    # VCF.debug()

    # Start overall timer
    timer_0 = timeit.default_timer()

    # MDR PARAMETERS
    mdr_config = {
        "bucket": config["root_path"],
        "samples_key": config["samples_file"],
        "patients_key": config["patients_file"],
        "output_key": f"{config['output_dir']}/nchks-{str(nchunks)}[{chunk_start}-{chunk_end}]",
        "plots": plots_dir,
        "chunk_start": chunk_start,
        "chunk_end": chunk_end,
        # "n_patients": 1128,
        "CV_sets": config["CV_sets"],
        "filter_imp": config["filter_imp"],  # FIXME unused?
        "prediction_power_tol": config["prediction_power_tol"],
    }

    # Compute all combinations
    print("Starting to compute all the combinations ...")
    print(f"Workers: {workers}, Chunks: {nchunks}, Range: {chunk_start}-{chunk_end}")
    compute_combinations(workers, nchunks, mdr_config)
    print(f"    > Total execution time {timeit.default_timer() - timer_0}")
