#!/bin/bash

fail_code=0
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
        fail_code=1
    fi
}

if [ "$#" -ne 2 ]; then
    echo "Use: rabbitmq_master_service.sh <start/stop> <rabbitmq.sif>"
    exit 1
fi

if [ "$1" = "start" ]; then
  # Start Singularity instance
  #mkdir -p ./var/{lib/rabbitmq,log}
  execute_command singularity instance start \
            -B etc/rabbitmq:/opt/rabbitmq_server-3.13.1/etc/rabbitmq \
            -B var/lib/rabbitmq:/opt/rabbitmq_server-3.13.1/var/lib/rabbitmq \
            -B var/log/rabbitmq:/opt/rabbitmq_server-3.13.1/var/log \
            $2 rabbitmq 

  #Add rabbitmq scripts to PATH 
  rabbimq_path="/opt/rabbitmq_server-3.13.1/sbin" 
  
  #Execute RabbitMQ server start command
  execute_command singularity exec instance://rabbitmq $rabbimq_path/rabbitmq-server -detached && sleep 30
  
  #Set new user and vhost
  execute_command singularity exec instance://rabbitmq $rabbimq_path/rabbitmqctl add_user 'admin1234' '1234'
  execute_command singularity exec instance://rabbitmq $rabbimq_path/rabbitmqctl add_vhost testadmin
  execute_command singularity exec instance://rabbitmq $rabbimq_path/rabbitmqctl set_permissions -p "testadmin" "admin1234" ".*" ".*" ".*"
  
  #Cluster status configuration
  execute_command singularity exec instance://rabbitmq $rabbimq_path/rabbitmqctl set_policy ha-all "" '{"ha-mode":"all","ha-sync-mode":"automatic"}'
  
  #Check final status 
  if [ $fail_code -eq 0 ]; then
    echo "*******************************"
    echo "RabbitMQ ready to run Lithops."
    echo "*******************************"

    while :; do
      #echo "RabbitMQ ready to running ..."
      sleep 600
    done

  else
    echo "**********************************************"
    echo "ERROR: RabbitMQ failed with above error code. "
    echo "**********************************************" 
    exit 1 
  fi
elif [ "$1" = "stop" ]; then
  execute_command singularity exec instance://rabbitmq  $rabbimq_path/rabbitmqctl shutdown
  execute_command singularity instance stop rabbitmq
  echo "*******************************"
  echo "RabbitMQ close."
  echo "*******************************"
else
    echo "Invalid argument. Use 'start' to start the instance or 'stop' to finish the user and virtual host."
    exit 1
fi

