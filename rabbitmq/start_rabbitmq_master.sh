#!/bin/bash

current_dir=$(pwd)
# Check if environment variables exist
if [ -z "$RABBITMQ_HOME" ]; then
    echo "export RABBITMQ_HOME environment variable with your RABBITMQ directory"
    exit 1
fi

if [ -z "$LITHOPS_CONFIG_FILE" ]; then
    echo "LITHOPS_CONFIG_FILE environment variable does not exist"
    cd $current_dir
    exit 1
fi

if [ -z "$HPC_USER" ]; then
    echo "export HPC_USER environment variable with your HPC slurm user-account"
    exit 1
fi
if [ -z "$HPC_QOS" ]; then
    echo "export HPC_QOS environment variable with HPC slurm partition"
    exit 1
fi

# Start RabbitMQ Master Node
echo "Starting RabbitMQ Master Node"
cd "$RABBITMQ_HOME" || exit
rm -rf data
mkdir -p data/var/{lib/rabbitmq,log/rabbitmq}
mkdir -p data/etc/rabbitmq
rmq_batch_job=$(sbatch --parsable -A "$HPC_USER" -q "$HPC_QOS" rabbitmq_master.slurm)
exit_code=$?
sleep 2
if [ $exit_code -ne 0 ]; then
    echo "Start RabbitMQ Master Node script failed."
    cd "$current_dir" || exit
    exit 1
fi
echo "$rmq_batch_job" >"rabbit.jid"
echo "OK-RMQ_Master"
echo "RabbitMQ Master job submitted, job_id:"
echo "$rmq_batch_job"

echo "Create a connection from the login node to the compute node"
while true; do
  JOB_STATE=$(squeue -j "$rmq_batch_job" -h -o "%T")
  if [ "$JOB_STATE" == "RUNNING" ]; then
    echo "Job $JOB_ID is now RUNNING."
    break
  else
    echo "Current state: $JOB_STATE. Waiting..."
    sleep 3
  fi
done

#Updating LITHOPS_CONFIG_FILE
rmq_node=$(squeue -j "$rmq_batch_job" -h -o "%R")
rmq_ip=$(grep ${rmq_node}-data /etc/hosts | cut -f1 -d " ")
echo "Setting Lithops Background for ${rmq_ip}"
current_rbmq=$(grep -v "#" $LITHOPS_CONFIG_FILE | grep "amqp_url" | cut -f4 -d":" | cut -f2 -d"@" | xargs)
sed -i "s/$current_rbmq/$rmq_ip/" "$LITHOPS_CONFIG_FILE"

# Forwarding RBMQ
echo "Forwarding RabbitMQ"
storage_root=$(grep -v "#" $LITHOPS_CONFIG_FILE | grep "storage_root" | cut -f2 -d":" | xargs)
storage_bucket=$(grep -v "#" $LITHOPS_CONFIG_FILE | grep "storage_bucket" | cut -f2 -d":" | xargs)
sockets_dir="$storage_root/$storage_bucket/sockets_dir"
rm -rf $sockets_dir/socket.sock
mkdir -p $sockets_dir
ssh -f -N -L $sockets_dir/socket.sock:localhost:5672 $rmq_node 
if [ $? -eq 0 ]; then
    echo "Tunnel established successfully."
else
    echo "Failed to create tunnel."
fi
sleep 10
echo "RabbitMQ DONE"
cd "$current_dir" || exit
