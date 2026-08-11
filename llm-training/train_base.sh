#!/bin/bash

# Configuration
export CUDA_VISIBLE_DEVICES=0
LOG_FILE="./llm-training/train_base.log"

echo "CUDA_VISIBLE_DEVICES is set to: $CUDA_VISIBLE_DEVICES"
echo "Logging to: $LOG_FILE"

# Execute training script
python llm-training/train_base.py 2>&1 | tee "$LOG_FILE"
