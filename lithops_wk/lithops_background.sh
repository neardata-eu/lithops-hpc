#!/bin/bash

# Function to execute a command in the background and wait for it to finish
execute_command() {
    echo "Executing command: $@"
    "$@" &
    local pid=$!
    wait "$pid"
    if [ $? -eq 0 ]; then
        echo "Command '$@' completed successfully."
    else
        echo "Command '$@' failed with exit code $?."
        exit 1
    fi
}

if [ "$#" -ne 3 ]; then
    echo "Use: $0 <start/stop> <RMQ_ip> <singularity-plantilla342.sif>"
    exit 1
fi

storage_bucket=$(grep -v "^#" lithops_config | grep "storage_bucket" | cut -f2 -d":" | cut -f1 -d"#")
storage_bucket=$(echo "$storage_bucket" | xargs)

echo "checking $storage_bucket"
if [ -d "$storage_bucket" ]; then
    echo "Using storage: $storage_bucket"
else
    echo "Storage$storage_bucket directory does not exist."
    exit 1
fi

if [ "$1" = "start" ]; then
  # Start singularity-plantilla instance
  execute_command singularity instance start -B $storage_bucket:$storage_bucket $3 lithops-worker
  sleep 30
  # Running background
  execute_command singularity run --env AMQP_URL=amqp://admin1234:1234@$2:5672/testadmin instance://lithops-worker

elif [ "$1" = "stop" ]; then
  execute_command singularity instance stop lithops-worker
  echo "*******************************"
  echo "lithops-worker close."
  echo "*******************************"
else
    echo "Invalid argument. Use 'start' to start the workers or 'stop' to finish the workers."
    exit 1
fi
