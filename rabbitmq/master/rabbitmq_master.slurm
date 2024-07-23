#!/bin/bash
#SBATCH --job-name=rabbitmq_master    				# Job name
#SBATCH --output=slurm_jobs/rmq_master_output_%j.txt      	# Output file (%j expands to jobID)
#SBATCH --error=slurm_jobs/rmq_master_error_%j.txt        	# Error file (%j expands to jobID)
#SBATCH --ntasks=1        					# Number of tasks (cores) per node
#SBATCH --cpus-per-task=10

# Load any necessary modules (e.g., for Python)
#module load singularity
conda activate lhops

# Start rabbitMQ master.sh <start/stop> <rabbitmq.sif> 
./rabbitmq_master_service.sh start $LITHOPS_HPC_HOME/sif/rabbitmq.sif
