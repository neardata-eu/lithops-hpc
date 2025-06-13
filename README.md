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

## Connect to a runtime (From client side)
#### 1. Start connection with HPC cluster
```bash
cd lithops-hpc
conda activate base-lithops
lithops hpc connect
```
#### 2. List all deployed runtime
```bash
lithops hpc runtime_list
```

## Deploy a new Compute Backend (From client side)
#### 1. Start RabbitMQ
```bash
lithops hpc start_rabbitmq_master
```
#### 2. Deploy runtime
```bash
lithops hpc runtime_deploy <runtime_name>
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
Lithops should be configured in the `lithops_config` file.
```bash
export LITHOPS_CONFIG_FILE=$LITHOPS_HPC_HOME/lithops_config
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[Apache V2.0]( http://www.apache.org/licenses/LICENSE-2.0)
