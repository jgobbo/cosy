#!/usr/bin/bash
#SBATCH --job-name=eoopt
#SBATCH --account=pc_eoopt
#SBATCH --partition=lr7
#SBATCH --qos=lr_normal
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=56
#SBATCH --cpus-per-task=1
#SBATCH --time=72:00:00

OUTPUT_DIR=~/outputs
mkdir -p "$OUTPUT_DIR"
exec > "$OUTPUT_DIR/${SLURM_JOB_ID}.out" 2>&1

source ~/cosy/.venv/bin/activate
python ~/cosy/scripts/slurm_optimize.py

