"""
Simple Lithops example using the map method.
In this example the map() method will launch one
map function for each entry in 'iterdata'. Finally
it will print the results for each invocation with
fexec.get_result()
"""
import lithops
import time
import argparse


def my_map_function(x):
    print("Hello World!")
    time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=int, help="Number of iterdata", default=8)
    args = parser.parse_args()
        
    iterdata = list(range(0,args.tasks))
    fexec = lithops.FunctionExecutor()
    
    start = time.time()
    future = fexec.map(my_map_function, iterdata)
    fexec.get_result()
    end = time.time()
    
    fexec.plot(dst="./plots_" + str(args.tasks))
    
    print(end - start)   
    
    with open("./output_" + str(args.tasks) + ".txt", "w+") as f:
        #print(f"--------------------- {end - start} ---------------------", file=f)
        for i in range(len(future)):
            print(future[i].stats, file=f)
    
    fexec.clean()
