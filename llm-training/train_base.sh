#!/bin/bash

# Find Conda python path and locate its site-packages/nvidia directory
CONDA_PYTHON="/mnt/hungpv/miniconda3/envs/carbench_env/bin/python"
NVIDIA_DIR="/mnt/hungpv/miniconda3/envs/carbench_env/lib/python3.10/site-packages/nvidia"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="$SCRIPT_DIR/train_base"

if [ -d "$NVIDIA_DIR" ]; then
    # Dynamically build LD_LIBRARY_PATH from all subdirectories containing lib
    LD_PATHS=$(find "$NVIDIA_DIR" -type d -name "lib" | paste -sd ":" -)
    export LD_LIBRARY_PATH="$LD_PATHS:$LD_LIBRARY_PATH"
    echo "Configured LD_LIBRARY_PATH with Nvidia packages' libraries."
fi

# Make sure CUDA_VISIBLE_DEVICES is set to 0 if not provided
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
echo "CUDA_VISIBLE_DEVICES is set to: $CUDA_VISIBLE_DEVICES"

# Auto-detect next available numbered log file
LOG_NUM=1
while [ -f "${LOG_PREFIX}_${LOG_NUM}.log" ]; do
    LOG_NUM=$((LOG_NUM + 1))
done
LOG_FILE="${LOG_PREFIX}_${LOG_NUM}.log"
echo "Logging to: $LOG_FILE"

# Run the training script, tee output to log file and stdout
$CONDA_PYTHON "$SCRIPT_DIR/train_base.py" "$@" 2>&1 | tee "$LOG_FILE"
