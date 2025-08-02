#!/usr/bin/bash
#SBATCH --job-name=eoopt
#SBATCH --account=pc_eoopt
#SBATCH --partition=lr4
#SBATCH --qos=lr_debug
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=5
#SBATCH --cpus-per-task=1
#
#SBATCH --time=10:00:00
#
uv run ./slurm_optimize.py

