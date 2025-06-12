# Lithops-HPC

## Installation (Client and provider)
#### 1. Obtain the Lithops-HPC code: clone the sources and set the ENV variables
```bash
git clone https://github.com/neardata-eu/lithops-hpc.git
cd lithops-hpc
export LITHOPS_HPC_HOME=$(pwd)
```
#### 2. Install dependencies in a mamba environment
```bash
conda install -n base -c conda-forge mamba
mamba env update -n base-lithops --file $LITHOPS_HPC_HOME/base-lithops.yml
conda activate base-lithops

# to deactivate or remove if necessary
conda deactivate
conda remove --name base-lithops --all
```

#### 3. Build Singularity Images 
```bash
cd $LITHOPS_HPC_HOME/rabbitmq/sif/
sudo singularity build rabbitmq4.sif rabbitmq4.def
export RABBITMQ_HOME=$LITHOPS_HPC_HOME/rabbitmq/
```

#### 4.Add environment variables to bashrc file
```bash
cd lithops-hpc
echo 'export LITHOPS_HPC_HOME=$(pwd)' >> ~/.bashrc
echo 'export RABBITMQ_HOME=$LITHOPS_HPC_HOME/rabbitmq/' >> ~/.bashrc
echo 'export LITHOPS_CONFIG_FILE=$LITHOPS_HPC_HOME/lithops_config' >> ~/.bashrc
echo 'export HPC_QOS=<slurm_queue>' >> ~/.bashrc
echo 'export HPC_USER=<slurm_user>' >> ~/.bashrc
source ~/.bashrc
```

## Compute Backend Deployment 
#### 1. Start RabbitMQ
```bash
cd lithops-hpc
conda activate base-lithops
module load singularity/4
rabbitmq/start_rabbitmq_master.sh
```
#### 2. Deploy runtime
```bash
lithops runtime deploy <runtime_name>
```

## Run Examples
```bash
cd lithops-hpc
conda activate base-lithops
cd $LITHOPS_HPC_HOME/examples/sleep 
mkdir -p plots
python sleep.py
```

## Configuration
Lithops should be configured in the `.lithops_config` file.
```bash
export LITHOPS_CONFIG_FILE=$LITHOPS_HPC_HOME/lithops_config
```

### Backends
The `.lithops_config` file contains a basic configuration to use the Lithops HPC backend. First, you must select the backends:
```yaml
lithops:
  backend: hpc
  storage: pfs
```
Optionally, you may set a custom function execution timeout and logging level:
```yaml
  execution_timeout: 180
  log_level: DEBUG
```

### Storage
You must also configure the storage backend:
```yaml
pfs:
  storage_root: /path/to/PFS/dir/
  storage_bucket: .storage
```
The storage root sets the location where all Lithops storage operations will work from.
It should point to a mounted PFS location accessible by client and backend nodes and it must be given as an **absolute path**.
Emulated storage buckets will become directories within the root.
The configured storage bucket is where Lithops internal files will reside (e.g., job status and intermediate data), and also the default location for objects through the Lithops Storage API.

For instance, you may use the `.storage` dir within this repo.



### HPC backend
You must configure at least one runtime to use the HPC backend.
```yaml
hpc:
  worker_processes: 112
  runtime: default
  runtimes:
    hpc-default:
      account: <hpc_account>
      qos: <hpc_qos>
      num_workers: 1
      cpus_worker: 112
      cpus_task: 1
```

The `worker_processes` key only sets the size of the RabbitMQ invocation message. It is best set as a multiple of the number of tasks that fit a worker. It means that, when configured to 112, if you run a Lithops map with 200 tasks (function invocations), two messages will be sent to RabbitMQ: one with 112 tasks and one with 88.

The `runtime` key is optional, by default set to `"default"`. It is used to designate which of the runtimes defined in the `runtimes` key will be used by default. If set to `"default"`, the first one is used.

The `runtimes` key should contain one or more Lithops workers slurm job definitions as a collection of dictionaries. The key of each dictionary (e.g., `hpc-default`) sets the runtime name. For each runtime, you must set the slurm user (`account`) and queue (`qos`), the number of Lithops workers to run (`num_workers`), and how many CPUs each worker will have (`cpus_worker`). Slurm will run each worker as a task with the specified CPU and calculate how many cluster nodes it needs. You may also set `cpus_task` to configure how much CPU to allocate for each Lithops task (and thus how many tasks fit concurrently on each worker), which by default is 1 to run as many tasks per worker as CPUs available in the worker.

Optionally, you may also set `max_time` for each runtime to define the maximum run time for the slurm job, 3 hours by default.
Also, you may set `rmq_queue` to change the task queue name for each runtime. This allows two or more runtimes to share a task queue and split work seamlessly. By default task queues take the runtime name, so in this example, you could define a second runtime `hpc2` and set its `rmq_queue` to `hpc-default` to share it with the first one.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[Apache V2.0]( http://www.apache.org/licenses/LICENSE-2.0)
