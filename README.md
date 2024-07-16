# Lithops_RabbitMQ

## Installation
#### 1. Obtain the Lithops_RabbitMQ code: clone the sources and set the ENV variables
```bash
git clone https://github.com/neardata-eu/Lithops-HPC.git
cd lithops-hpc
export LITHOPS_HPC_HOME=$(pwd)
```
#### 2. Install dependencies in a mamba environment
```bash
conda install -n base -c conda-forge mamba
mamba env update -n lhops --file $LITHOPS_HPC_HOME/lhops.yml
conda activate lhops

# to deactivate or remove if necessary
conda deactivate
conda remove --name lhops --all
```

#### 3. Build Singularity Images
```bash
cd $LITHOPS_HPC_HOME/sif/
lithops runtime build -b singularity singularity-plantilla321
sudo singularity build rabbitmq.sif rabbitmq.def
```

## Usage 
num_lithops_workers=num_cpus x num_nodes
```bash
cd lithops_rabbitmq
export LITHOPS_HPC_HOME=$(pwd)
export MN5_QOS=<MN5_Partition>
export MN5_USER=<MN5_ACCOUNT>
export PATH=$LITHOPS_HPC_HOME/scripts:$PATH
export LITHOPS_CONFIG_FILE=$LITHOPS_HPC_HOME/lithops_wk/lithops_config

conda activate lhops
lithops_hpc.sh <num_cpus> <num_nodes>
```

## Run Examples
```bash
cd examples/sleep 
mkdir plots
sbatch -A $MN5_USER -q $MN5_QOS job.slurm
```
## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[Apache V2.0]( http://www.apache.org/licenses/LICENSE-2.0)
