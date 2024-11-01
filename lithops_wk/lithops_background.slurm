#!/bin/bash

#SBATCH --job-name=CPU_workers_lithops      		# Job name
#SBATCH --output=slurm_jobs/output_%j.txt      	# Output file (%j expands to jobID)
#SBATCH --error=slurm_jobs/error_%j.txt        	# Error file (%j expands to jobID)


# Check if input arguments are provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <rabbitmq_ip>"
    exit 1
fi
NGINX_HOSTNAME=$1

export SRUN_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK}
export LITHOPS_CONFIG_FILE=$LITHOPS_HPC_STORAGE/lithops_config

# Load any necessary modules (e.g., for Python)
conda activate lhops

srun python $LITHOPS_HPC_HOME/scripts/lithopsentry.py amqp://admin1234:1234@$NGINX_HOSTNAME:5672/testadmin
#Running lithops_background.sh <start/stop> <nginx_ip> <singularity-plantilla.sif> 
#srun  lithops_background.sh start $NGINX_HOSTNAME $LITHOPS_HPC_HOME/sif/singularity-plantilla342.sif
