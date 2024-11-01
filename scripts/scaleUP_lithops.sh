#!/bin/bash

current_dir=$(pwd)

if [ -z "$MN5_USER" ]; then
    echo "export MN5_USER environment variable with your MN5 user-account"
    cd $current_dir
    exit 1
fi

if [ -z "$MN5_QOS" ]; then
    echo "export MN5_QOS environment variable with MN5 partition"
    cd $current_dir
    exit 1
fi

# Check if LITHOPS_HPC_HOME environment variable exists
if [ -z "$LITHOPS_HPC_HOME" ]; then
    echo "LITHOPS_HPC_HOME environment variable does not exist"
    cd $current_dir
    exit 1
fi

# Check if LITHOPS_CONFIG_FILE environment variable exists
if [ -z "$LITHOPS_CONFIG_FILE" ]; then
    echo "LITHOPS_CONFIG_FILE environment variable does not exist"
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
nginx_hostname=$(squeue -o "%9i %.60j %R" | grep $nginx_job |  rev | cut -d " " -f1 | rev)

cpus=$2
nodes=$3

#1. Allocate new nodes
cd $LITHOPS_HPC_HOME/lithops_wk
lithops_job=$(sbatch --parsable --dependency=after:$nginx_job -A $MN5_USER -q $MN5_QOS -c $cpus -N $nodes -n $nodes lithops_background.slurm $nginx_hostname )
if [ $? -ne 0 ]; then
  echo "Setting new nodes to failed."
  cd $current_dir
  exit 1
fi

#2.1. Configure Lithops Background
echo "Setting Lithops Background"
current_workers=$(grep -v "#" $LITHOPS_CONFIG_FILE | grep "worker_processes" | cut -f2 -d":" | xargs)
new_workers=$(echo "$current_workers+($cpus * $nodes)" | bc)
sed -i "s/worker_processes: $current_workers/worker_processes: $new_workers/" "$LITHOPS_CONFIG_FILE"

echo "Setting new nodes:$nodes cpusxnode:$cpus, total workers:$new_workers"
echo "DONE"
cd $current_dir
