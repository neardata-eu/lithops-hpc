#!/bin/bash
#SBATCH --job-name=os_bmk2x48_lithops    # Job name
#SBATCH --output=slurm_jobs/output_%j.txt      # Output file (%j expands to jobID)
#SBATCH --error=slurm_jobs/error_%j.txt        # Error file (%j expands to jobID)
#SBATCH --nodes=1                   # Number of nodes
#SBATCH --ntasks-per-node=1        # Number of tasks (cores) per node
#SBATCH --cpus-per-task=2           # Number of CPU cores per task

export LITHOPS_CONFIG_FILE=$LITHOPS_HPC_HOME/lithops_wk/lithops_config

# Load any necessary modules (e.g., for Python)
#module load python/3.10.2
conda activate lhops

# Run the Python script
python os_benchmark.py run -b singularity -s localhost --mb_per_file=512 --bucket_name=storage --number=96 --outdir=plots
