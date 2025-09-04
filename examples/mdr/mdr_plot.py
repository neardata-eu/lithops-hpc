import json
import os
import time

import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import pylab
import seaborn as sns
from matplotlib.collections import LineCollection

sns.set_style("whitegrid")
pylab.switch_backend("Agg")


def create_timeline(results, dst, figsize=(10, 6)):
    job_results = results["job_results"]
    worker_results = results["worker_results"]

    for stat in worker_results:
        stat["mdr_breakdown"] = np.array(stat["mdr_breakdown"])
    stats_df = pd.DataFrame(worker_results)
    total_calls = len(stats_df)
    # print(stats_df.mdr_breakdown)
    times = stats_df.mdr_breakdown
    # min_time = times.map(lambda a: a[0, 0]).min()
    min_time = job_results["start_tstmp"]
    max_time = (times.map(lambda a: a[-1, -1]).max() - min_time) * 1.25

    read_times = []
    compute_times = []
    write_times = []
    for worker_times in times:
        for pair_times in worker_times:
            read_times.append(pair_times[1] - pair_times[0])
            compute_times.append(pair_times[2] - pair_times[1])
            write_times.append(pair_times[3] - pair_times[2])

    print("Chunk pair stats")
    print(f"Average read time: {np.mean(read_times)} s")
    print(f"Average compute time: {np.mean(compute_times)} s")
    print(f"Average write time: {np.mean(write_times)} s")
    print("")

    palette = sns.color_palette("deep", 10)

    fig = pylab.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)

    # y = np.arange(total_calls)
    # point_size = 10

    times = times - min_time
    # print(times)

    # fields = [
    #     ("pair init", times.map(lambda row: row[:, 0])),
    #     ("pair read", times.map(lambda row: row[:, 1])),
    #     ("pair compute", times.map(lambda row: row[:, 2])),
    #     ("pair write", times.map(lambda row: row[:, 3])),
    # ]

    read_segments = []
    comp_segments = []
    writ_segments = []
    for i, row in enumerate(times):
        i += 1  # skip 0 for driver line
        init = row[:, 0]
        read = row[:, 1]
        comp = row[:, 2]
        writ = row[:, 3]
        for j in range(len(init)):
            read_segments.append([[init[j], i], [read[j], i]])
            comp_segments.append([[read[j], i], [comp[j], i]])
            writ_segments.append([[comp[j], i], [writ[j], i]])

    preproc_segments = [
        [
            [job_results["start_tstmp"] - min_time, 0],
            [job_results["preproc_tstmp"] - min_time, 0],
        ],
    ]
    wait_segments = [
        [
            [job_results["preproc_tstmp"] - min_time, 0],
            [job_results["end_tstmp"] - min_time, 0],
        ],
    ]

    patches = []
    # Preproc:
    line_segments = LineCollection(preproc_segments, linestyles="solid", color=palette[0], alpha=0.8, linewidth=2)
    ax.add_collection(line_segments)
    patches.append(mpatches.Patch(color=palette[0], label="preprocessing"))
    # Driver waiting:
    line_segments = LineCollection(wait_segments, linestyles="solid", color=palette[4], alpha=0.8, linewidth=2)
    ax.add_collection(line_segments)
    patches.append(mpatches.Patch(color=palette[4], label="wait"))

    # Workers breakdown:
    line_segments = LineCollection(read_segments, linestyles="solid", color=palette[1], alpha=0.8, linewidth=2)
    ax.add_collection(line_segments)
    patches.append(mpatches.Patch(color=palette[1], label="read time"))
    line_segments = LineCollection(comp_segments, linestyles="solid", color=palette[2], alpha=0.8, linewidth=2)
    ax.add_collection(line_segments)
    patches.append(mpatches.Patch(color=palette[2], label="compute time"))
    line_segments = LineCollection(writ_segments, linestyles="solid", color=palette[3], alpha=0.8, linewidth=2)
    ax.add_collection(line_segments)
    patches.append(mpatches.Patch(color=palette[3], label="write time"))

    # for f_i, (field_name, val) in enumerate(fields):
    #     for i, val_row in enumerate(val):
    #         for ts in val_row:
    #             ax.scatter(
    #                 ts,
    #                 y[i],
    #                 c=[palette[f_i]],
    #                 edgecolor="none",
    #                 s=point_size,
    #                 alpha=0.8,
    #             )
    #     patches.append(mpatches.Patch(color=palette[f_i], label=field_name))

    ax.set_xlabel("Execution Time (sec)")
    ax.set_ylabel("Worker ID")

    legend = pylab.legend(handles=patches, loc="upper right", frameon=True)
    legend.get_frame().set_facecolor("#FFFFFF")

    yplot_step = int(np.max([1, total_calls / 20]))
    y_ticks = np.arange(total_calls // yplot_step + 2) * yplot_step
    y_labels = ["Driver"] + list(map(str, y_ticks))
    y_labels.pop()
    ax.set_yticks(y_ticks, y_labels)
    ax.set_ylim(-0.02 * total_calls, total_calls * 1.02)
    for y in y_ticks:
        ax.axhline(y, c="k", alpha=0.1, linewidth=1)

    xplot_step = max(int(max_time / 8), 1)
    x_ticks = np.arange(max_time // xplot_step + 2) * xplot_step
    ax.set_xlim(0, max_time)

    ax.set_xticks(x_ticks)
    for x in x_ticks:
        ax.axvline(x, c="k", alpha=0.2, linewidth=0.8)

    ax.grid(False)
    fig.tight_layout()

    if dst is None:
        os.makedirs("plots", exist_ok=True)
        dst = os.path.join(os.getcwd(), "plots", "{}_{}".format(int(time.time()), "breakdown.pdf"))
    else:
        dst = os.path.expanduser(dst) if "~" in dst else dst
        dst = "{}_{}".format(os.path.realpath(dst), "breakdown.pdf")

    fig.savefig(dst)


if __name__ == "__main__":
    results_file = "plots/scaling/synthetic_1.8MSNP_1f_1128p-15-1000[0-5]-d6da09-0-results.json"
    output_prefix = "plots/scaling/synthetic_1.8MSNP_1f_1128p-15-1000[0-5]-d6da09-0"

    if not os.path.exists(results_file):
        raise FileNotFoundError(f"{results_file} does not exist!")

    results = json.load(open(results_file, "r"))
    job_results = results["job_results"]
    worker_results = results["worker_results"]

    preproc_time = job_results["preproc_tstmp"] - job_results["start_tstmp"]
    job_time = job_results["total_time"]
    work_time = job_results["end_tstmp"] - job_results["preproc_tstmp"]
    workers = job_results["num_workers"]

    print(f"Job completed in {job_time} s")
    print(f"Preprocessing in {preproc_time} s")

    times = []
    pairs = []
    candidates = []
    breakdowns = []
    for result in worker_results:
        if result is not None:
            times.append(result["total_time"])
            pairs.append(result["total_pairs"])
            candidates.append(result["candidate_pairs"])
            breakdowns.append(result["mdr_breakdown"])

    total_pairs = sum(pairs)
    total_candidates = sum(candidates)

    if times:
        print(f"MDR-function times. Max: {max(times)}")  # to take the worst-case
        print(f"MDR applied to a total of {total_pairs} pairs")
        print(f"Found a total of {total_candidates} candidate pairs")
        print(f"Total COMBS/SEC: {total_pairs / job_time}")
        print(f"Total COMBS/SEC/CORE: {total_pairs / job_time / workers}")
        print(f"Without preprocessing. Time: {work_time}")
        print(f"Total COMBS/SEC: {total_pairs / work_time}")
        print(f"Total COMBS/SEC/CORE: {total_pairs / work_time / workers}")
    else:
        print("MDR functions failed. No results.")

    print("")
    plots_dir = os.path.dirname(results_file)

    create_timeline(results, output_prefix)
