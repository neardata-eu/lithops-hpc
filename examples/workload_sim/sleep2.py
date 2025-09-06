import lithops
import time
import argparse


def my_map_function(x, sleep_time):
    print(f"Task {x}: Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=int, help="Number of tasks", default=8)
    parser.add_argument("--sleep", type=int, help="Sleep time per task in seconds", default=5)
    args = parser.parse_args()

    iterdata = [(i, args.sleep) for i in range(args.tasks)]  # pass both index and sleep time

    fexec = lithops.FunctionExecutor()

    start = time.time()
    future = fexec.map(my_map_function, iterdata)  # unpack tuple (x, sleep_time)
    fexec.get_result()
    end = time.time()

    fexec.plot(dst=f"./plots_{args.tasks}")

    print(f"Total elapsed time: {end - start:.2f} seconds")

    with open(f"./output_{args.tasks}.txt", "w+") as f:
        for i in range(len(future)):
            print(future[i].stats, file=f)

    fexec.clean()
