
import torch
import functools
from mpi4py import MPI


"""
Decorator to set the device based on user choice and GPU availability, defaults to CPU.
Default to CPU unless GPU is requested and available
"""
def set_device(device, gpus):
  def decorator(func):
    @functools.wraps(func)
    def wrapper(id,*args,**kwargs):
      device_choice = "cpu"
      gpu_id = 0  
      if device == "gpu" and torch.cuda.is_available():
        gpu_id = id % gpus
        device_choice = f"cuda:{gpu_id}"
      
      func.__globals__['device'] = device_choice
      func.__globals__['gpu_id'] = gpu_id
        
      return func(id,*args,**kwargs)
    return wrapper
  return decorator

"""
Decorator to use MPI communication system.

"""  
def mpi_comm_decorator(comm,id_rank):
  def decorator(func):
    @functools.wraps(func)
    def wrapper(id,*args,**kwargs):
      
      comm = MPI.COMM_WORLD
      
      for arg in kwargs.values():
        color = 0 if arg==None else 1
           
      comm2 = comm.Split(color)
      rank = comm2.Get_rank()
      size = comm2.Get_size()
      
      
      #Skipping execution for None values 
      for arg in kwargs.values():
        if arg==None:
          return None
      
      #Updating the rank 
      data={id:rank}
      all_ranks = []
      if rank == 0:
        all_ranks.append(data)
        for i in range(1, size):
          all_ranks.append(comm2.recv(source=i))   
      else:
        comm2.send(data, dest=0)  
  
      all_ranks = comm2.bcast(all_ranks, root=0)
      id_rank = {key: value for d in all_ranks for key, value in d.items()}
      func.__globals__['id_rank'] = id_rank
      func.__globals__['comm'] = comm2
      print(f"id_rank: {id_rank}")
        
      return func(id,*args,**kwargs)
    return wrapper
  return decorator

"""
Complementary data 
"""  
def generate_iterdata(iterdata, tasks, workers):
    m = (tasks % workers)
    m = (workers - m) % workers
    for i in range(m):
        iterdata.append(None)
    return iterdata  
