#!/bin/bash

job_id=$(cat ".rabbitmq/rabbit.jid")
echo "Cancelling job $job_id . . ."
scancel "$job_id"
