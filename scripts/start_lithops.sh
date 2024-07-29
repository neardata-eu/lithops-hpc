#!/bin/bash

current_dir=$(pwd)
# Check if LITHOPS_HPC_HOME environment variable exists
if [ -z "$LITHOPS_HPC_HOME" ]; then
    echo "LITHOPS_HPC_HOME environment variable does not exist"
    cd $current_dir
    exit 1
fi

# Check if input arguments are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <rmq_job_id> <num_cpus> <num_nodes>"
    cd $current_dir
    exit 1
fi
nginx_job=$1
nginx_hostname=$(squeue | grep $nginx_job |  rev | cut -d " " -f1 | rev)

cpus=$2
nodes=$3

#cpusxcore=112
#nodes=$(echo "($workers+$cpusxcore+1)/$cpusxcore" | bc)
#cpus=$(echo "($workers)/$nodes" | bc)

workers=$(echo "$cpus * $nodes" | bc)
echo "Setting nodes:$nodes cpusxnode:$cpus, total workers:$workers"

#3.1. Configure Lithops Background
echo "Setting Lithops Background"
cd $LITHOPS_HPC_HOME/lithops_wk

# Check if LITHOPS_HPC_STORAGE environment variable is set
if [ -z "$LITHOPS_HPC_STORAGE" ]; then
    export LITHOPS_HPC_STORAGE=$LITHOPS_HPC_HOME/lithops_wk/storage
    echo "LITHOPS_HPC_STORAGE environment variable set to : $LITHOPS_HPC_STORAGE"

else
    echo "LITHOPS_HPC_STORAGE environment variable already set to: $LITHOPS_HPC_STORAGE"
fi
mkdir -p $LITHOPS_HPC_STORAGE
touch $LITHOPS_HPC_STORAGE/lithops_config    
cat << EOF > $LITHOPS_HPC_STORAGE/lithops_config

lithops:
    backend : singularity
    storage: localhost
    monitoring: rabbitmq
    log_level: INFO

rabbitmq: 
    amqp_url: amqp://admin1234:1234@$nginx_hostname:5672/testadmin

singularity:
    runtime: singularity-plantilla342
    sif_path: $LITHOPS_HPC_HOME/sif
    worker_processes: $workers

localhost:
    storage_bucket: $LITHOPS_HPC_STORAGE
EOF

lithops_job=$(sbatch --parsable --dependency=after:$nginx_job -A $MN5_USER -q $MN5_QOS -c $cpus -N $nodes -n $nodes lithops_background.slurm $nginx_hostname )
if [ $? -ne 0 ]; then
  echo "Setting Lithops failed."
  cd $current_dir
  exit 1
fi
echo "$lithops_job" > $LITHOPS_HPC_HOME/jobs/lithops_job_id.txt
echo "Lithops running on $lithops_hostname job_id: $lithops_job"
cd $current_dir
