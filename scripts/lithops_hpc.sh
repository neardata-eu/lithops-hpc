#!/bin/bash

current_dir=$(pwd)

# Function to execute a command in the background and wait for it to finish
execute_command() {
    fail_code=0
    echo "Executing command: $@"
    "$@" &
    local pid=$!
    wait "$pid"
    if [ $? -eq 0 ]; then
        echo "Command '$@' completed successfully."
    else
        echo "Command '$@' failed with exit code $?."
        fail_code=1
    fi
}

# Check if the file exisist and is not empty
check_file(){
    some_file=$1
    if [ ! -f "$some_file" ]; then
        echo "File $some_file not found."
        cd $current_dir
        exit 1
    fi

    if [ ! -s "$some_file" ]; then
        echo "File $some_file is empty."
        cd $current_dir
        exit 1
    fi
}

# Check if the service is running
wait_for_job() {
    local job_id=$1
    local max_loops=10
    local loop_counter=0
    echo "Check the status of the job: $job_id"
    while true; do
        status=$(squeue -h -j "$job_id" -o "%T")
        if [ "$status" = "RUNNING" ]; then
            echo "Job $job_id is now running."
            break
        fi
        sleep 5
    
        ((loop_counter++))
        # Check if maximum loops reached
        if [ "$loop_counter" -gt "$max_loops" ]; then
            echo "Something was wrong. Exiting..."
            cd $current_dir
    	    exit 1
            break
        fi
    done
}

# Check if the activated Conda environment is 'lhops'
if [[ "$(basename "$CONDA_PREFIX")" != "lhops" ]]; then
    echo "The activated Conda environment is not 'lhops'."
    cd $current_dir
    exit 1
fi

# Check if Lithops_HPC_HOME environment variable exists
if [ -z "$LITHOPS_HPC_HOME" ]; then
    echo "LITHOPS_HPC_HOME environment variable does not exist"
    cd $current_dir
    exit 1
fi

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

# Check if input arguments are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <num_cpus> <num_nodes>"
    cd $current_dir
    exit 1
fi
cpus=$1
nodes=$2

#### 1. Set Up RabbitMQ Cluster
#### 1.1. Start RabbitMQ Master Node
echo "Starting RabbitMQ-Master node . . ."
execute_command $LITHOPS_HPC_HOME/scripts/start_rabbitmq_master.sh
master_job_id_file=$LITHOPS_HPC_HOME/jobs/master_job_id.txt
check_file $master_job_id_file
master_job_id=$(cat $master_job_id_file)
wait_for_job $master_job_id
echo "RabbitMQ Master node ready"
echo ""
echo ""
#### 3. Set Up Lithops backend
echo "Starting Lithops backend . . ."
execute_command $LITHOPS_HPC_HOME/scripts/start_lithops.sh $master_job_id $cpus $nodes
lithops_job_id_file=$LITHOPS_HPC_HOME/jobs/lithops_job_id.txt
check_file $lithops_job_id_file
lithops_job_id=$(cat $lithops_job_id_file)
wait_for_job $lithops_job_id
echo "Lithops backend running"
echo ""
echo ""
sleep 30
echo "OK-"
echo "RabbitMQ and Lithophs are running"
