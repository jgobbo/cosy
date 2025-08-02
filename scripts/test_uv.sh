#!/usr/bin/bash
srun -p lr4 -A pc_eoopt -q lr_normal -N 1 -t 00:10:00 --pty uv run python

