import numpy as np
import time
import csv
import socket
import argparse
from mpi4py import MPI

# Function to perform the FLOPS benchmark and return elapsed time and peak GFLOPS
def flops_benchmark(id,loopcount,MAT_N):
    A = np.arange(MAT_N**2, dtype=np.float64).reshape(MAT_N, MAT_N)
    B = np.arange(MAT_N**2, dtype=np.float64).reshape(MAT_N, MAT_N)

    start = time.time()
    for i in range(loopcount):
        c = np.sum(np.dot(A, B))

    FLOPS = 2 * MAT_N**3 * loopcount
    end = time.time()
    total_time = end-start
    #print(f"{id},{total_time:.2f},{(FLOPS/1e9/total_time):.2f}")    
    return total_time, FLOPS


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot FLOPS benchmark results from a CSV file.")
    #parser.add_argument("--tasks", type=int, help="how many tasks",default=10)
    parser.add_argument("--loopcount", type=int, help="Number of matmuls to do",default=6)
    parser.add_argument("--matn", type=int, help="size of matrix",default=1024)

    args = parser.parse_args()
    #tasks = args.tasks  # Number of parallel instances to run
    loopcount = args.loopcount 
    MAT_N = args.matn 
    
    # Get the host name
    host_name = socket.gethostname()

    # Use a pool of workers to run multiple instances concurrently
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Run benchmark
    elapsed_time, flop_count = flops_benchmark(rank, loopcount, MAT_N)

    # Compute GFLOPS
    gflops = flop_count / 1e9 / elapsed_time
    local_result = (rank, elapsed_time, gflops)
    all_results = comm.gather(local_result, root=0)
    
    # Rank 0 computes and prints summary
    if rank == 0:
        csv_file_name = f"flops_results_{host_name}_{size}.csv"
        avg_gflops = sum(g[2] for g in all_results) / len(all_results)
        peak_gflops = max(g[2] for g in all_results)
        total_time = max(g[1] for g in all_results)

        with open(csv_file_name, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Instance", "Elapsed Time (s)", "GFLOPS"])
            for row in all_results:
                writer.writerow(row)
            # writer.writerow([])
            # writer.writerow([f"Summary for {size} tasks"])
            # writer.writerow(["Average GFLOPS", f"{avg_gflops:.2f}"])
            # writer.writerow(["Peak GFLOPS", f"{peak_gflops:.2f}"])
            # writer.writerow(["Execution time", f"{total_time:.2f}"])

        print(f"Execution time for {size} instances: {total_time:.2f}")
        print(f"Average GFLOPS across {size} instances: {avg_gflops:.2f}")
        print(f"Peak GFLOPS across {size} instances: {peak_gflops:.2f}")
        
    
