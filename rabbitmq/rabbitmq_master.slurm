#!/bin/bash
#SBATCH --job-name=rmq_master               # Job name (%x)
#SBATCH --output=slurm_jobs/%x_%j.out.log   # Output file (%j expands to jobID)
#SBATCH --error=slurm_jobs/%x_%j.err.log    # Error file (%j expands to jobID)
#SBATCH --ntasks=1                          # Number of tasks (cores) per node
#SBATCH --cpus-per-task=16

# Start rabbitMQ master.sh <start/stop> <rabbitmq.sif>
./rabbitmq_master_service.sh start "sif/rabbitmq4.sif"
