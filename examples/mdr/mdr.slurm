#!/bin/bash
#SBATCH --job-name=mdr_lithops                          # Job name
#SBATCH --output=slurm_jobs/mdr_%j.out.log              # Output file (%j expands to jobID)
#SBATCH --error=slurm_jobs/mdr_%j.err.log               # Error file (%j expands to jobID)
#SBATCH --nodes=1                                       # Number of nodes
#SBATCH --ntasks-per-node=1                             # Number of tasks (cores) per node
#SBATCH --cpus-per-task=112                             # Number of CPU cores per task
#SBATCH --time=00:10:00                                 # Time limit hrs:min:sec

# Run the Python script
python mdr.py "$@"
