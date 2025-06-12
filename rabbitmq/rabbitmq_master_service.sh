#!/bin/bash

# fail_code=0
# Function to execute a command in the background and wait for it to finish
execute_command() {
    echo "Executing command: '$*'"
    "$@" &
    local pid=$!
    wait "$pid"
    status=$?
    if [ $status -eq 0 ]; then
        echo "Command '$*' completed successfully."
    else
        echo "Command '$*' failed with exit code $status."
        # fail_code=1
    fi
}

if [ "$#" -ne 2 ]; then
    echo "Use: rabbitmq_master_service.sh <start/stop> <rabbitmq.sif>"
    exit 1
fi


if [ "$1" = "start" ]; then
    # Start Singularity instance
    execute_command singularity instance start \
        -B data/etc/rabbitmq:/etc/rabbitmq \
        -B data/var/lib/rabbitmq:/var/lib/rabbitmq \
        -B data/var/log/rabbitmq:/var/log/rabbitmq \
        "$2" rabbitmq

    # Run instance runscript (blocking)
    execute_command singularity run instance://rabbitmq
elif [ "$1" = "stop" ]; then
    execute_command singularity exec instance://rabbitmq rabbitmqctl shutdown
    execute_command singularity instance stop rabbitmq
    echo "*******************************"
    echo "RabbitMQ close."
    echo "*******************************"
else
    echo "Invalid argument. Use 'start' to start the instance or 'stop' to finish the user and virtual host."
    exit 1
fi
