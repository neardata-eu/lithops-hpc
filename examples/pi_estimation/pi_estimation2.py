#!/usr/bin/env python
# coding: utf-8

import lithops
import numpy as np
import time
import pickle as pickle

def monte_carlo_pi_estimation(n):
    np.random.seed()
    inside_circle = 0
    for _ in range(n):
        x, y = np.random.random(), np.random.random()
        if x**2 + y**2 <= 1.0:  # Radius is 1.0
            inside_circle += 1
    pi_estimate = (inside_circle / n) * 4
    return pi_estimate, n * 4  # 4 operations per iteration

def compute_flops(_):
    iterations = 10**7  # Number of iterations for Monte Carlo simulation
    start_time = time.time()
    pi_estimate, flops = monte_carlo_pi_estimation(iterations)
    end_time = time.time()
    
    time_taken = end_time - start_time
    return flops, time_taken, pi_estimate

if __name__ == "__main__":
    program_start_time = time.time()
    fexec = lithops.FunctionExecutor()

    # Run the benchmark function 10 times in parallel
    n_runs = 2240
    futures = fexec.map(compute_flops, [None] * n_runs)  
    results = fexec.get_result(futures)
    
    worker_stats = [f.stats for f in futures if not f.error]
    
    total_flops = sum(res[0] for res in results)
    avg_time = sum(res[1] for res in results) / len(results)
    pi_estimates = [res[2] for res in results]
    
    # Calculate GFLOPS per CPU
    gflops_per_second = total_flops / avg_time 
    avg_pi_estimate = sum(pi_estimates) / len(pi_estimates)
    
    program_end_time = time.time()
    running_time=program_end_time-program_start_time
    
    res = {'start_time': program_start_time,
           'total_time': running_time,
           'est_flops': gflops_per_second,
           'worker_stats': worker_stats,
           'results': total_flops,
           'workers': n_runs,
           'loopcount': 10**6,
           'MATN': 0}
    
    pickle.dump(res, open(f'stats2.pickle', 'wb'))
    
    print(f'Total FLOPS: {total_flops}')
    print(f'AVG Time: {avg_time} seconds')
    print(f'FLOPS per CPU: {gflops_per_second}')
    print(f'Average Pi Estimate: {avg_pi_estimate}')
    print(f'Running time: {running_time}')


