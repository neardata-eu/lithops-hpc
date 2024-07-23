#!/bin/bash

current_dir=$(pwd)
# Check if LITHOPS_HPC_HOME environment variable exists
if [ -z "$LITHOPS_HPC_HOME" ]; then
    echo "LITHOPS_HPC_HOME environment variable does not exist"
    exit 1
fi

#1.1. Start RabbitMQ Master Node
echo "Starting RabbitMQ Master Node"
cd $LITHOPS_HPC_HOME/rabbitmq/master/
rm -rf var etc
mkdir -p ./var/{lib/rabbitmq,log/rabbitmq}
mkdir -p etc/rabbitmq
master_batch_job=$(sbatch --parsable -A $MN5_USER -q $MN5_QOS rabbitmq_master.slurm)
sleep 2
if [ $? -ne 0 ]; then
    echo "Start RabbitMQ Master Node script failed."
    cd $LITHOPS_HPC_HOME
    exit 1
fi
echo "$master_batch_job" > $LITHOPS_HPC_HOME/jobs/master_job_id.txt
echo "OK-RMQ_Master"
echo "RabbitMQ Master running, job_id: $master_batch_job"
cd $current_dir
