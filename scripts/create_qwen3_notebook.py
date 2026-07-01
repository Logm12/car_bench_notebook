import json
import os

notebook = {
 "cells": [],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

def add_markdown(text):
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    })

def add_code(code_str):
    lines = code_str.splitlines(keepends=True)
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines
    })

# --- Add Notebook Cells ---

add_markdown("""# Evaluating Qwen3-8B on CAR-bench

This notebook implements the evaluation pipeline for the **Qwen3-8B-Instruct** model on the **CAR-bench** dataset. CAR-bench is a benchmark designed to assess in-car voice assistants on action-oriented tasks, handling user inputs, system context, policies, hallucination detection, and interactive disambiguation.

To run efficiently in cloud environments like Google Colab (T4 GPUs) or Kaggle:
- We deploy an optimized 4-bit quantized version: `unsloth/Qwen3-8B-bnb-4bit` (with `Qwen/Qwen3-8B-AWQ` as a fallback option) using the **vLLM** inference engine.
- We implement strict memory management controls to avoid Out-Of-Memory (OOM) errors.
- We establish an automated checkpoint-merging state recovery mechanism. If the Colab kernel restarts or disconnects, re-running the notebook will resume execution exactly where it left off, avoiding duplicate execution and API calls.""")

add_markdown("""## 1. Environment Setup

We determine our run environment (Google Colab, Kaggle, or local workspace), clone the official CAR-bench repository, install package dependencies via `uv`, and append paths to `sys.path` to avoid `ModuleNotFoundError` issues.""")

add_code(r"""import os
import sys

# Detect execution environment
try:
    import google.colab
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

# Clone repository if running in a clean cloud VM
if IN_COLAB or not os.path.exists("src"):
    print("Cloning repository to retrieve wiki.md policy and scripts...")
    !git clone --recursive https://github.com/CAR-bench/car-bench-ijcai.git
    %cd car-bench-ijcai
else:
    print("Running in local workspace.")

# Resolve third-party submodule dependencies
if not os.path.exists("third_party/car-bench/pyproject.toml"):
    print("Submodule files missing in third_party/car-bench. Restoring...")
    !git submodule update --init --recursive
    if not os.path.exists("third_party/car-bench/pyproject.toml"):
        print("Submodule check failed. Cloning official repository directly...")
        import shutil
        if os.path.exists("third_party/car-bench"):
            try:
                shutil.rmtree("third_party/car-bench")
            except Exception:
                !rm -rf third_party/car-bench
        !git clone --depth 1 https://github.com/CAR-bench/car-bench.git third_party/car-bench""")

add_code(r"""# Install the uv package manager and required dependencies
print("Installing dependencies...")
!pip install -q uv
!uv pip install --system -q a2a-sdk[http-server]>=1.0.0 httpx loguru pydantic python-dotenv uvicorn nest-asyncio matplotlib pandas seaborn psutil datasets bitsandbytes>=0.45.0 litellm
!uv pip install --system -e third_party/car-bench
!uv pip install --system -q vllm""")

add_markdown("""## 2. Resource Monitoring & Memory Purging

To prevent GPU Out-of-Memory (OOM) errors and host RAM overflow during model loading and evaluation, we define helper functions to log usage statistics and purge PyTorch CUDA allocation caches.""")

add_code(r'''import gc
import torch
import psutil
import socket
import os
import subprocess

# Dummy GPU operation to register active GPU usage with Colab resource monitor
if torch.cuda.is_available():
    print(f"Active GPU: {torch.cuda.get_device_name(0)}")
    _dummy = torch.zeros((1, 1), device="cuda")
else:
    print("WARNING: GPU is not available. Please switch runtime to GPU.")

def is_port_in_use(port):
    """Checks if a port is in use locally."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def cleanup_ports(ports=[8080, 8081]):
    """Kills processes on target ports safely and quickly, protecting the notebook session."""
    my_pid = os.getpid()
    my_ppid = os.getppid()
    protected_pids = {my_pid, my_ppid}
    
    print(f"Scanning for active processes on ports: {ports}...")
    for port in ports:
        if not is_port_in_use(port):
            continue
        print(f"Port {port} is in use. Identifying process...")
        pids_to_kill = set()
        
        # Identify PIDs using target port using OS command (much faster than iterating all processes)
        try:
            if os.name == 'nt':
                cmd = f"netstat -ano | findstr :{port}"
                try:
                    output = subprocess.check_output(cmd, shell=True).decode()
                    for line in output.strip().split('\\n'):
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            # Usually netstat output format: Proto LocalAddress ForeignAddress State PID
                            # If state is not present, PID could be at index 4, otherwise at index 4 or 5
                            pid_candidate = parts[-1]
                            try:
                                pid = int(pid_candidate)
                                if pid not in protected_pids:
                                    pids_to_kill.add(pid)
                            except ValueError:
                                pass
                except subprocess.CalledProcessError:
                    pass
            else:
                try:
                    pids_str = subprocess.check_output(["lsof", "-ti", f":{port}"]).decode().split()
                    for pid_str in pids_str:
                        try:
                            pid = int(pid_str)
                            if pid not in protected_pids:
                                pids_to_kill.add(pid)
                        except ValueError:
                            pass
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
        except Exception as e:
            print(f"Error identifying process for port {port}: {e}")
            
        # Fallback to psutil only for specific connections if OS tools failed
        if not pids_to_kill:
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.laddr.port == port and conn.pid:
                        if conn.pid not in protected_pids:
                            pids_to_kill.add(conn.pid)
            except Exception:
                pass
                
        # Filter identified PIDs to ensure safety before terminating
        for pid in list(pids_to_kill):
            try:
                proc = psutil.Process(pid)
                cmdline = proc.cmdline()
                cmd_str = " ".join(cmdline).lower()
                name = proc.name().lower()
                
                # Double check to protect Jupyter/Notebook itself
                if any(k in name or k in cmd_str for k in ["jupyter", "ipykernel", "colab"]):
                    print(f"Skipping protected PID {pid} ({proc.name()}) on port {port}.")
                    pids_to_kill.discard(pid)
                    continue
                    
                # Ensure it matches expected safe keywords to avoid killing system/user services
                is_safe_to_kill = any(kw in cmd_str or kw in name for kw in ["vllm", "server.py", "track_1", "evaluator", "car-bench", "ollama"])
                if not is_safe_to_kill:
                    print(f"Skipping PID {pid} ({proc.name()}) on port {port} (does not match safe keywords).")
                    pids_to_kill.discard(pid)
            except Exception:
                pids_to_kill.discard(pid)

        # Execute termination on safely identified PIDs
        for pid in pids_to_kill:
            try:
                proc = psutil.Process(pid)
                print(f"Terminating safe process {proc.name()} (PID {pid}) on port {port}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    print(f"Process {pid} terminated successfully.")
                except psutil.TimeoutExpired:
                    print(f"Process {pid} did not exit. Force killing...")
                    proc.kill()
                    proc.wait(timeout=2)
            except Exception as e:
                print(f"Failed to terminate PID {pid}: {e}")

cleanup_ports()
purge_memory()
print_resource_usage()''')

add_markdown("""## 3. Persistent Checkpointing & Checkpoint Merging

We mount Google Drive (if running on Colab) or configure a persistent output folder. We then implement a robust checkpoint-merging utility. 
This script reads the target output JSON (`qwen3_8b_benchmark.json`), checks which tasks have already completed successfully, and allows the run loop to skip them, preventing duplicate executions and minimizing API usage.""")

add_code(r'''PERSISTENT_DIR = "./output"
if IN_COLAB:
    try:
        from google.colab import drive
        print("Mounting Google Drive for persistent artifact backups...")
        drive.mount('/content/drive')
        PERSISTENT_DIR = "/content/drive/MyDrive/car_bench_eval_qwen3"
    except Exception as e:
        print(f"Google Drive mount failed: {e}. Output will be saved locally.")
elif os.path.exists("/kaggle/working"):
    PERSISTENT_DIR = "/kaggle/working/output"

os.makedirs(PERSISTENT_DIR, exist_ok=True)
print(f"Target persistent directory: {PERSISTENT_DIR}")''')

add_code(r'''import json
from datasets import load_dataset

# Configuration for evaluation splits (5 tasks per split for benchmark)
target_splits = {
    "base": 5,
    "hallucination": 5,
    "disambiguation": 5
}

def get_all_task_ids():
    """Retrieves standard task IDs from the Hugging Face dataset."""
    all_task_ids = {}
    for task_type, limit in target_splits.items():
        try:
            config_name = f"tasks_{task_type}"
            ds = load_dataset("johanneskirmayr/car-bench-dataset", config_name, split="train")
            all_task_ids[task_type] = [ds[i]["task_id"] for i in range(min(limit, len(ds)))]
        except Exception as e:
            print(f"Dataset download skipped or failed for {task_type}: {e}. Using fallback IDs.")
            all_task_ids[task_type] = [f"{task_type}_{i}" for i in range(limit)]
    return all_task_ids

def merge_and_save_results(main_file_path, temp_file_path):
    """Merges new trial runs into the main persistent benchmark JSON file."""
    if not os.path.exists(temp_file_path):
        print("No temporary results file found to merge.")
        return
    
    try:
        with open(temp_file_path, "r") as f:
            new_data = json.load(f)
    except Exception as e:
        print(f"Failed to read new results: {e}")
        return
        
    merged_data = {}
    if os.path.exists(main_file_path):
        try:
            with open(main_file_path, "r") as f:
                merged_data = json.load(f)
        except Exception as e:
            print(f"Failed to read existing checkpoint: {e}. Starting fresh.")
            
    if not merged_data:
        merged_data = {
            "metadata": new_data.get("metadata", {}),
            "summary_text": "",
            "summary": {},
            "final_result": {
                "score": 0.0,
                "max_score": 0,
                "pass_rate": 0.0,
                "task_rewards_by_split": {
                    "base": {},
                    "hallucination": {},
                    "disambiguation": {}
                },
                "pass_power_k_scores_by_split": {},
                "pass_at_k_scores_by_split": {},
                "detailed_results_by_split": {
                    "base": [],
                    "hallucination": [],
                    "disambiguation": []
                }
            },
            "results": [],
            "artifacts": []
        }
        
    # Merge results list
    existing_results = {r.get("task_id"): r for r in merged_data.get("results", []) if r.get("task_id")}
    for r in new_data.get("results", []):
        if r.get("task_id"):
            existing_results[r["task_id"]] = r
    merged_data["results"] = list(existing_results.values())
    
    # Merge detailed split results
    detailed_merged = merged_data["final_result"].setdefault("detailed_results_by_split", {
        "base": [], "hallucination": [], "disambiguation": []
    })
    detailed_new = new_data.get("final_result", {}).get("detailed_results_by_split", {})
    for split in ["base", "hallucination", "disambiguation"]:
        tasks_dict = {t.get("task_id"): t for t in detailed_merged.get(split, []) if t.get("task_id")}
        for t in detailed_new.get(split, []):
            if t.get("task_id"):
                tasks_dict[t["task_id"]] = t
        detailed_merged[split] = list(tasks_dict.values())
        
    # Merge task rewards
    rewards_merged = merged_data["final_result"].setdefault("task_rewards_by_split", {
        "base": {}, "hallucination": {}, "disambiguation": {}
    })
    rewards_new = new_data.get("final_result", {}).get("task_rewards_by_split", {})
    for split in ["base", "hallucination", "disambiguation"]:
        rewards_merged.setdefault(split, {}).update(rewards_new.get(split, {}))
        
    # Recompute metrics
    all_completed = []
    for split in ["base", "hallucination", "disambiguation"]:
        all_completed.extend(detailed_merged.get(split, []))
        
    total_reward = sum(t.get("reward", 0.0) for t in all_completed)
    num_completed = len(all_completed)
    pass_rate = (total_reward / num_completed * 100) if num_completed > 0 else 0.0
    
    merged_data["final_result"]["score"] = total_reward
    merged_data["final_result"]["max_score"] = num_completed
    merged_data["final_result"]["pass_rate"] = pass_rate
    merged_data["final_result"]["pass_power_k_scores"] = {"Pass^1": pass_rate / 100.0}
    merged_data["final_result"]["pass_at_k_scores"] = {"Pass@1": pass_rate / 100.0}
    
    # Update split-level pass rate
    merged_data["final_result"]["pass_power_k_scores_by_split"] = {}
    merged_data["final_result"]["pass_at_k_scores_by_split"] = {}
    for split in ["base", "hallucination", "disambiguation"]:
        split_tasks = detailed_merged.get(split, [])
        if split_tasks:
            split_reward = sum(t.get("reward", 0.0) for t in split_tasks)
            split_rate = split_reward / len(split_tasks)
            merged_data["final_result"]["pass_power_k_scores_by_split"][split] = {"Pass^1": split_rate}
            merged_data["final_result"]["pass_at_k_scores_by_split"][split] = {"Pass@1": split_rate}
            
    # Rebuild the final summary text
    summary_parts = [
        "CAR-bench Evaluation Summary",
        f"Tasks Evaluated: {num_completed}",
        f"Overall Pass Rate: {pass_rate:.1f}% ({total_reward:.1f}/{num_completed})",
        "",
        "Pass Metrics:",
        f"  Pass^1 (Pass@1): {pass_rate:.1f}%",
        "",
        "Split Breakdown:"
    ]
    for split in ["base", "hallucination", "disambiguation"]:
        split_tasks = detailed_merged.get(split, [])
        if split_tasks:
            split_reward = sum(t.get("reward", 0.0) for t in split_tasks)
            split_rate = (split_reward / len(split_tasks) * 100)
            summary_parts.append(f"  - {split.capitalize()}: {split_rate:.1f}% ({split_reward:.1f}/{len(split_tasks)})")
            for t in sorted(split_tasks, key=lambda x: x.get("task_id", "")):
                summary_parts.append(f"    * Task {t['task_id']}: {'✓' if t.get('reward', 0.0) >= 0.99 else '✗'} ({t.get('reward', 0.0):.2f})")
                
    merged_data["summary_text"] = "\n".join(summary_parts)
    
    with open(main_file_path, "w") as f:
        json.dump(merged_data, f, indent=2)
    print(f"Checkpoint successfully updated at {main_file_path}")''')

add_markdown("""## 4. Local vLLM Inference Server

We configure and run the `vLLM` server serving the optimized `unsloth/Qwen3-8B-bnb-4bit` (or `Qwen/Qwen3-8B-AWQ`) locally on port 8000. 
We configure strict memory-safety limits:
- `--gpu-memory-utilization 0.70` (leaves 30% GPU memory for the rest of PyTorch, evaluator, user simulator).
- `--max-model-len 8000` (limits max context tokens to bound KV cache memory).

We check if the vLLM server is already running to support safe cell re-runs. If it is already online, we reuse it. Otherwise, we spawn it as a background subprocess and poll its health endpoint until it is fully ready.""")

add_code(r'''import time
import subprocess
import httpx
import sys
import psutil

# Choose model:
# "unsloth/Qwen3-8B-bnb-4bit" - Optimized 4-bit bnb version (default)
# "Qwen/Qwen3-8B-AWQ" - Optimized 4-bit AWQ version (alternative)
VLLM_MODEL = "unsloth/Qwen3-8B-bnb-4bit"
VLLM_PORT = 8000

vllm_already_running = False
is_vllm_loading = False

# Query the local port to see if a model server is already responsive or loading
if is_port_in_use(VLLM_PORT):
    print(f"Port {VLLM_PORT} is in use. Checking occupying process...")
    cmdline = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                for conn in proc.connections(kind='inet'):
                    if conn.laddr.port == VLLM_PORT:
                        cmdline = proc.info.get('cmdline') or []
                        break
            except Exception:
                pass
            if cmdline:
                break
    except Exception:
        pass
        
    is_vllm_proc = any("vllm" in str(arg).lower() for arg in cmdline)
    
    if is_vllm_proc:
        try:
            response = httpx.get(f"http://localhost:{VLLM_PORT}/v1/models", timeout=2)
            if response.status_code == 200:
                print("vLLM server is already active and responsive. Reusing it.")
                vllm_already_running = True
            else:
                print("vLLM process detected but returned non-200. Assuming it is loading...")
                is_vllm_loading = True
        except Exception:
            print("vLLM process detected but unresponsive. Assuming it is loading...")
            is_vllm_loading = True
    else:
        print(f"Port {VLLM_PORT} is occupied by a non-vLLM process. Terminating it...")
        cleanup_ports([VLLM_PORT])

vllm_proc = None
if not vllm_already_running and not is_vllm_loading:
    print(f"Launching vLLM background process with model: {VLLM_MODEL}...")
    vllm_cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", VLLM_MODEL,
        "--port", str(VLLM_PORT),
        "--gpu-memory-utilization", "0.70",
        "--max-model-len", "8000"
    ]
    
    # Append quantization parameters if using bitsandbytes
    if "bnb" in VLLM_MODEL:
        vllm_cmd.extend(["--quantization", "bitsandbytes", "--load-format", "bitsandbytes"])
        
    log_file_path = "vllm_server.log"
    vllm_log = open(log_file_path, "w")
    vllm_proc = subprocess.Popen(vllm_cmd, stdout=vllm_log, stderr=vllm_log)
    
    # Check for immediate crash (e.g. exit code non-zero due to unsupported quantization flags in older vLLM)
    time.sleep(5)
    exit_code = vllm_proc.poll()
    if exit_code is not None:
        print(f"vLLM server exited immediately with code {exit_code}. Retrying with fallback configuration (removing bnb flags)...")
        vllm_log.close()
        
        # Fallback configuration: remove bitsandbytes load format and quantization options
        vllm_cmd = [arg for arg in vllm_cmd if arg not in ["--quantization", "bitsandbytes", "--load-format", "bitsandbytes"]]
        vllm_log = open(log_file_path, "w")
        vllm_proc = subprocess.Popen(vllm_cmd, stdout=vllm_log, stderr=vllm_log)
        
        # Check fallback crash
        time.sleep(5)
        if vllm_proc.poll() is not None:
            print("vLLM fallback server also exited immediately. Startup failed.")
            if os.path.exists(log_file_path):
                with open(log_file_path, "r") as f:
                    print("".join(f.readlines()[-20:]))
            raise RuntimeError("vLLM fallback startup failed.")

if not vllm_already_running:
    print("Waiting for vLLM server to start up (monitoring health endpoint)...")
    is_ready = False
    for attempt in range(45):
        try:
            response = httpx.get(f"http://localhost:{VLLM_PORT}/v1/models", timeout=2)
            if response.status_code == 200:
                print(f"\nvLLM server is now active and listening on port {VLLM_PORT}!")
                is_ready = True
                break
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(10)
        
    if not is_ready:
        print("\n[ERROR] vLLM server did not start in time.")
        log_file_path = "vllm_server.log"
        if os.path.exists(log_file_path):
            print("\n--- Last 30 lines of vllm_server.log ---")
            with open(log_file_path, "r") as f:
                lines = f.readlines()
                print("".join(lines[-30:]))
        raise RuntimeError("vLLM startup failed.")''')

add_markdown("""## 5. Credentials Configuration

We request the user's Gemini API Key. The User Simulator (simulating the driver) and the Policy Evaluator (judging policy constraints) both utilize Gemini API models.""")

add_code(r'''import getpass

print("Enter your Gemini API Key:")
gemini_key = getpass.getpass()

# Write variables to the local .env configuration file
with open(".env", "w") as f:
    f.write(f"GEMINI_API_KEY={gemini_key}\n")
    f.write(f"OPENAI_API_BASE=http://localhost:{VLLM_PORT}/v1\n")
    f.write("OPENAI_API_KEY=local-dummy-key\n")

print("Created .env file successfully.")''')

add_markdown("""## 6. Execution Loop with State Recovery

We check existing checkpoints, filter out completed tasks, write a temporary TOML scenario containing only the remaining tasks, and call `car-bench-run`. 
After the run is complete, we merge the new results back into the persistent file.""")

add_code(r'''import os
import sys

# Determine Python runtime executable path
if IN_COLAB or os.path.exists("/kaggle/working"):
    python_path = sys.executable
else:
    python_path = os.path.abspath(".venv/bin/python")
    if os.name == 'nt':
        python_path = os.path.abspath(".venv/Scripts/python.exe")
    if not os.path.exists(python_path):
        python_path = sys.executable

python_path_formatted = python_path.replace('\\', '/')
print(f"Using Python runtime: {python_path_formatted}")

# Configure path to main result file
main_result_file = os.path.join(PERSISTENT_DIR, "qwen3_8b_benchmark.json")

# Determine total target tasks and completed tasks
all_task_ids = get_all_task_ids()
total_target_tasks = sum(len(ids) for ids in all_task_ids.values())

completed_ids = set()
if os.path.exists(main_result_file):
    try:
        with open(main_result_file, "r") as f:
            old_data = json.load(f)
        detailed = old_data.get("final_result", {}).get("detailed_results_by_split", {})
        for split, tasks in detailed.items():
            for t in tasks:
                if "task_id" in t:
                    completed_ids.add(t["task_id"])
    except Exception as e:
        print(f"Failed to read existing checkpoint results: {e}. Starting fresh.")

print(f"Progress: {len(completed_ids)}/{total_target_tasks} tasks completed.")

# Check for remaining tasks
remaining_tasks = {}
for split, task_ids in all_task_ids.items():
    remaining_tasks[split] = [tid for tid in task_ids if tid not in completed_ids]
    print(f"  {split.capitalize()} split: {len(remaining_tasks[split])} tasks remaining.")

total_remaining = sum(len(ids) for ids in remaining_tasks.values())

if total_remaining == 0:
    print("All tasks have already been completed successfully!")
else:
    # Generate scenario TOML string
    lines = [
        "# Dynamic CAR-bench scenario config for Qwen3-8B-Instruct",
        "[evaluator]",
        'endpoint = "http://127.0.0.1:8081"',
        f'cmd = "{python_path_formatted} src/evaluator/server.py --host 127.0.0.1 --port 8081"',
        "",
        "[agent_under_test]",
        'endpoint = "http://127.0.0.1:8080"',
        f'cmd = "{python_path_formatted} src/track_1_agent_under_test/server.py --host 127.0.0.1 --port 8080 --agent-llm openai/{VLLM_MODEL} --temperature 0.0"',
        "",
        "[config]",
        "num_trials = 1",
        'task_split = "train"',
        "max_steps = 30",
        'user_model = "gemini/gemini-2.5-flash"',
        'user_provider = "gemini"',
        'policy_evaluator_model = "gemini/gemini-2.5-flash"',
        'policy_evaluator_provider = "gemini"'
    ]
    
    for split, task_ids in remaining_tasks.items():
        if task_ids:
            lines.append(f"tasks_{split}_task_id_filter = {json.dumps(task_ids)}")
            
    temp_toml_path = "scenarios/track_1_agent_under_test/qwen3_temp_scenario.toml"
    os.makedirs(os.path.dirname(temp_toml_path), exist_ok=True)
    with open(temp_toml_path, "w") as f:
        f.write("\n".join(lines))
        
    print(f"Generated scenario TOML configuration for {total_remaining} remaining tasks.")
    temp_output_path = "output/qwen3_temp_output.json"
    os.makedirs("output", exist_ok=True)
    if os.path.exists(temp_output_path):
        os.remove(temp_output_path)''')

add_markdown("""### 6.1 Run Evaluation CLI

We clean up any leftover agent/evaluator ports and execute the benchmark run using the official `uv run car-bench-run` tool.""")

add_code(r'''# Clean up leftover agent/evaluator ports before running
cleanup_ports([8080, 8081])

# Run the benchmark scenario using the official BTC syntax
!uv run car-bench-run scenarios/track_1_agent_under_test/qwen3_temp_scenario.toml --output output/qwen3_temp_output.json --show-logs''')

add_markdown("""### 6.2 Checkpoint Consolidation and Memory Cleanup

We load the newly generated results, merge them into our main checkpoint file, and purge the system and GPU memory.""")

add_code(r'''# Merge results and cleanup memory
if os.path.exists("output/qwen3_temp_output.json"):
    merge_and_save_results(main_result_file, "output/qwen3_temp_output.json")
else:
    print("No new evaluation output found to merge.")

purge_memory()''')

add_markdown("""## 7. Results Visualization and Comparison

We load our final consolidated results and compare them directly against Qwen2.5-Coder-7B-Instruct (local baseline) and other models on the CAR-bench leaderboard.""")

add_code(r'''import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from IPython.display import display, HTML

# Locate main consolidated results file
main_result_file = os.path.join(PERSISTENT_DIR, "qwen3_8b_benchmark.json")

if not os.path.exists(main_result_file) and os.path.exists("output/qwen3_temp_output.json"):
    main_result_file = "output/qwen3_temp_output.json"

try:
    with open(main_result_file, "r") as f:
        data = json.load(f)
        
    final_result = data.get("final_result", {})
    pass_rate = final_result.get("pass_rate", 0.0)
    rewards_by_split = final_result.get("pass_power_k_scores_by_split", {})
    
    # Extract split-level scores
    splits = ["base", "hallucination", "disambiguation"]
    split_scores = []
    for split in splits:
        split_score = rewards_by_split.get(split, {}).get("Pass^1", 0.0) * 100
        split_scores.append(split_score)
        
    print("=== FINAL CONSOLIDATED SCORES ===")
    print(f"Overall Pass Rate: {pass_rate:.1f}%")
    print(f"Base Split Pass Rate: {split_scores[0]:.1f}%")
    print(f"Hallucination Split Pass Rate: {split_scores[1]:.1f}%")
    print(f"Disambiguation Split Pass Rate: {split_scores[2]:.1f}%")
    
    # Plot results
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    categories = ["Overall", "Base Split", "Hallucination Split", "Disambiguation Split"]
    values = [pass_rate] + split_scores
    
    ax = sns.barplot(x=categories, y=values, palette="viridis")
    plt.title("CAR-bench Scores (Qwen3-8B-Instruct)", fontsize=14, fontweight="bold", pad=15)
    plt.ylabel("Pass Rate (%)", fontsize=12)
    plt.ylim(0, 100)
    
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height() + 1.5),
                    ha='center', va='center', fontsize=11, fontweight="semibold", color='black', xytext=(0, 5),
                    textcoords='offset points')
                    
    plt.tight_layout()
    chart_path = os.path.join(PERSISTENT_DIR, "qwen3_scores.png")
    plt.savefig("output/qwen3_scores.png", dpi=300)
    plt.savefig(chart_path, dpi=300)
    plt.show()
    
    # Leaderboard comparison
    comparison_data = {
        "Model": [
            "Claude Opus 4.6",
            "GPT-5",
            "Gemini 2.5 Pro",
            "Qwen3-8B-Instruct (This Run)",
            "Qwen2.5-Coder-7B-Instruct (Baseline)",
            "Qwen3-32B",
            "xLAM-2-32B"
        ],
        "Alignment Method": [
            "RLHF",
            "RLHF",
            "RLHF",
            "Raw SFT/RLHF",
            "Raw (Unaligned)",
            "Base SFT/RLHF",
            "SFT/DPO"
        ],
        "Overall Pass Rate": [
            "58.0%",
            "54.0%",
            "38.0%",
            f"{pass_rate:.1f}%",
            "20.0%",
            "31.0%",
            "16.0%"
        ]
    }
    
    df = pd.DataFrame(comparison_data)
    display(HTML("<h3>CAR-bench Leaderboard Comparison</h3>"))
    display(df)
    
except Exception as e:
    print(f"Visualization error: {e}. Ensure that results are available and correctly formatted.")''')

add_markdown("""## 8. Graceful Shutdown & Resource Cleanup

To free up all host resources, we explicitly terminate the spawned vLLM server subprocess.""")

add_code(r'''if vllm_proc is not None:
    print("Stopping local vLLM background process...")
    try:
        vllm_proc.terminate()
        vllm_proc.wait(timeout=10)
        print("vLLM process stopped successfully.")
    except Exception as e:
        print(f"Failed to terminate vLLM cleanly: {e}. Killing process...")
        vllm_proc.kill()
else:
    print("No active vLLM subprocess managed by this notebook instance to shut down.")''')

# --- Save Notebook to File ---

os.makedirs("notebooks", exist_ok=True)
notebook_path = "notebooks/qwen3_coder_8b_benchmark.ipynb"
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Created notebook successfully at {notebook_path}")
