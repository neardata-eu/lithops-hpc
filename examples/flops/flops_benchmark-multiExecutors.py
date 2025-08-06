#
# Copyright Cloudlab URV 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import click
import time
import numpy as np
import pickle as pickle
from mpi4py import MPI

from lithops import FunctionExecutor
from plots import (
    create_execution_histogram,
    create_rates_histogram,
    create_total_gflops_plot,
)


def compute_flops(loopcount, MAT_N):
    A = np.arange(MAT_N**2, dtype=np.float64).reshape(MAT_N, MAT_N)
    B = np.arange(MAT_N**2, dtype=np.float64).reshape(MAT_N, MAT_N)

    start = time.time()
    for i in range(loopcount):
        c = np.sum(np.dot(A, B))  # noqa: F841

    FLOPS = 2 * MAT_N**3 * loopcount

    end = time.time()

    return {"flops": FLOPS / (end - start)}


# def benchmark(backend, storage, workers, memory, loopcount, matn, debug):
#     iterable = [(loopcount, matn) for i in range(workers)]
#     log_level = "INFO" if not debug else "DEBUG"
#     fexec = FunctionExecutor(backend=backend, storage=storage, runtime_memory=memory, log_level=log_level)
#     start_time = time.time()
#     worker_futures = fexec.map(compute_flops, iterable)
#     results = fexec.get_result(throw_except=False)
#     end_time = time.time()
#     results = [flops for flops in results if flops is not None]
#     worker_stats = [f.stats for f in worker_futures if not f.error]
#     total_time = end_time - start_time

#     print("Total time:", round(total_time, 3))
#     toal_executed_tasks = len(worker_stats)
#     est_flops = toal_executed_tasks * 2 * loopcount * matn**3
#     print("Estimated GFLOPS:", round(est_flops / 1e9 / total_time, 4))

#     res = {
#         "start_time": start_time,
#         "total_time": total_time,
#         "est_flops": est_flops,
#         "worker_stats": worker_stats,
#         "results": results,
#         "workers": toal_executed_tasks,
#         "loopcount": loopcount,
#         "MATN": matn,
#     }

#     return res


def benchmark(backend, storage, workers, memory, loopcount, matn, debug):
    log_level = "INFO" if not debug else "DEBUG"
    max_workers_per_executor = 896

    # MPI setup
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    num_batches = (workers + max_workers_per_executor - 1) // max_workers_per_executor
    print(f'num_batches:{num_batches}')
    # All ranks must call gather, even if they do no work
    if rank < num_batches:
        batch_start = rank * max_workers_per_executor
        batch_end = min(batch_start + max_workers_per_executor, workers)
        batch_size = batch_end - batch_start

        iterable = [(loopcount, matn) for _ in range(batch_size)]

        print(f"[Rank {rank}] Launching executor with {batch_size} workers...")
        print(iterable[0])
        
        fexec = FunctionExecutor(backend=backend, storage=storage,
                                 runtime_memory=memory, log_level=log_level)

        batch_start_time = time.time()
        batch_futures = fexec.map(compute_flops, iterable)
        batch_results = fexec.get_result(throw_except=False)
        batch_end_time = time.time()

        # Process results
        batch_results = [flops for flops in batch_results if flops is not None]
        batch_stats = [f.stats for f in batch_futures if not f.error]
        batch_total_time = batch_end_time - batch_start_time
        batch_executed = len(batch_stats)
        batch_flops = batch_executed * 2 * loopcount * matn**3
        
    else:
        batch_results = []
        batch_stats = []
        batch_total_time = 0.0
        batch_flops = 0
        batch_executed = 0
    
    # All ranks must participate
    all_results = comm.gather(batch_results, root=0)
    all_stats = comm.gather(batch_stats, root=0)
    all_flops = comm.gather(batch_flops, root=0)
    all_times = comm.gather(batch_total_time, root=0)
    all_counts = comm.gather(batch_executed, root=0)

    if rank == 0:
        global_start_time = time.time() - max(all_times)  # approximate global start
        total_time = max(all_times)
        total_flops = sum(all_flops)
        total_workers = sum(all_counts)

        print("\nMPI Benchmark Summary")
        print("----------------------")
        print("Total workers executed:", total_workers)
        print("Total time:", round(total_time, 3), "seconds")
        print("Estimated GFLOPS:", round(total_flops / 1e9 / total_time, 4))
        
        res= {
            "start_time": global_start_time,
            "total_time": total_time,
            "est_flops": total_flops,
            "worker_stats": [s for batch in all_stats for s in batch],
            "results": [r for batch in all_results for r in batch],
            "workers": total_workers,
            "loopcount": loopcount,
            "MATN": matn,
        }
        pickle.dump(res, open(f"multiexecutor.pickle", "wb"))
        return res
    return {}  # non-root ranks return an empty dict


def create_plots(data, outdir, name):
    create_execution_histogram(data, "{}/{}_execution.png".format(outdir, name))
    create_rates_histogram(data, "{}/{}_rates.png".format(outdir, name))
    create_total_gflops_plot(data, "{}/{}_gflops.png".format(outdir, name))


@click.command()
@click.option("--backend", "-b", default=None, help="compute backend name", type=str)
@click.option("--storage", "-s", default=None, help="storage backend name", type=str)
@click.option("--tasks", default=10, help="how many tasks", type=int)
@click.option("--memory", default=1024, help="Memory per worker in MB", type=int)
@click.option("--outdir", default=".", help="dir to save results in")
@click.option("--name", help="filename to save results in")
@click.option("--loopcount", default=6, help="Number of matmuls to do.", type=int)
@click.option("--matn", default=1024, help="size of matrix", type=int)
@click.option("--debug", "-d", is_flag=True, help="debug mode")
def run_benchmark(backend, storage, tasks, memory, outdir, name, loopcount, matn, debug):
    name = "{}_flops".format(tasks) if name is None else name
    if True:
        res = benchmark(backend, storage, tasks, memory, loopcount, matn, debug)
        pickle.dump(res, open(f"{outdir}/{name}.pickle2", "wb"))
    else:
        res = pickle.load(open(f"{outdir}/{name}.pickle", "rb"))
    #create_plots(res, outdir, name)


if __name__ == "__main__":
    run_benchmark()
