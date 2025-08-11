#!/usr/bin/bash
#SBATCH --job-name=eoopt
#SBATCH --account=pc_eoopt
#SBATCH --partition=lr4
#SBATCH --qos=lr_normal
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --cpus-per-task=1
#
#SBATCH --time=24:00:00
##SBATCH --error=~/outputs/slurm_optimize.out
##SBATCH --output=~/outputs/slurm_optimize.out
#
uv run ./slurm_optimize.py

