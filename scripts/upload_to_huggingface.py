#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "huggingface_hub>=0.20.0",
# ]
# ///
"""
Hugging Face dataset uploader for CAR-Bench SFT datasets.
Uploads car_base_sft.jsonl, car_disambiguation_sft.jsonl, car_hallucination_sft.jsonl,
and car_sft_dataset_openai.jsonl to upwitu/carbench_sft_benchmark_data.
"""

import os
import sys
from huggingface_hub import HfApi, create_repo

REPO_ID = "upwitu/carbench_sft_benchmark_data"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

FILES_TO_UPLOAD = [
    "car_base_sft.jsonl",
    "car_disambiguation_sft.jsonl",
    "car_hallucination_sft.jsonl",
    "car_sft_dataset_openai.jsonl",
    "car_sft_dataset.jsonl"
]

def main():
    token = os.environ.get("HF_TOKEN")
    api = HfApi(token=token)
    
    print(f"[INFO] Target Hugging Face Repository: https://huggingface.co/datasets/{REPO_ID}")
    try:
        create_repo(repo_id=REPO_ID, repo_type="dataset", exist_ok=True, token=token)
        print("[SUCCESS] Dataset repository ready on Hugging Face.")
    except Exception as e:
        print(f"[WARN] Repo creation status: {e}")

    for file_name in FILES_TO_UPLOAD:
        local_path = os.path.join(DATA_DIR, file_name)
        if not os.path.exists(local_path):
            print(f"[SKIP] Local file not found: {local_path}")
            continue

        file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
        print(f"[UPLOADING] {file_name} ({file_size_mb:.2f} MB)...")
        try:
            api.upload_file(
                path_or_fileobj=local_path,
                path_in_repo=f"data/{file_name}",
                repo_id=REPO_ID,
                repo_type="dataset",
                token=token
            )
            print(f"[COMPLETED] Uploaded data/{file_name} successfully!")
        except Exception as e:
            print(f"[ERROR] Failed to upload {file_name}: {e}")

if __name__ == "__main__":
    main()
