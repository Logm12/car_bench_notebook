"""
CAR-bench Trajectory Extraction Utility.

Parses evaluation JSON log files, extracts successful trajectories (reward >= 0.99),
reconstructs the system prompts (including location/datetime replacements), and outputs
a JSONL file formatted for supervised fine-tuning (SFT) with tool definitions.
"""
import os
import sys
import io
import glob
import json
import argparse
from pathlib import Path

# Force stdout/stderr to use UTF-8 on Windows to prevent encoding crashes with emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add third_party/car-bench to path to allow importing from car_bench
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "third_party" / "car-bench"))
sys.path.insert(0, str(WORKSPACE_ROOT))

try:
    from car_bench.envs.car_voice_assistant.tools import ALL_TOOLS
    from car_bench.envs.car_voice_assistant.wiki import WIKI_RAW
    from car_bench.envs.tool_manipulation import remove_tool_elements
except ImportError:
    print("WARNING: Could not import car_bench library. Trajectory tools extraction will fall back to skeleton.")
    ALL_TOOLS = []
    WIKI_RAW = ""
    def remove_tool_elements(tools, base, removed): return tools


def compact_json_dumps(obj):
    """Serialize dictionary to a compact JSON string without whitespace."""
    return json.dumps(obj, separators=(',', ':'))


def reconstruct_system_prompt(context_init_config):
    """Reconstruct system prompt by populating wiki placeholders with task config."""
    if not WIKI_RAW:
        return "You are a helpful in-car voice assistant."
    
    # Parse coordinates/datetime from context_init_config
    location = context_init_config.get("current_location", {})
    location_str = compact_json_dumps(location)
    
    datetime_val = context_init_config.get("current_datetime", {})
    datetime_str = compact_json_dumps(datetime_val)
    
    wiki = WIKI_RAW
    wiki = wiki.replace("INS:", "").replace("AUT-POL:", "").replace("LLM-POL:", "")
    
    wiki = wiki.replace("{{placeholder_location_based_on_task_context_init_config}}", location_str)
    wiki = wiki.replace("{{placeholder_datetime_based_on_task_context_init_config}}", datetime_str)
    return wiki


def get_task_runs(log_data):
    """Helper to extract flat task runs from various log file structures."""
    if isinstance(log_data, list):
        return log_data
    if not isinstance(log_data, dict):
        return []
        
    task_runs = []
    
    # 1. Check final_result -> detailed_results_by_split (standard evaluator server consolidated output)
    final_result = log_data.get("final_result")
    if isinstance(final_result, dict):
        detailed = final_result.get("detailed_results_by_split")
        if isinstance(detailed, dict):
            for split, task_list in detailed.items():
                if isinstance(task_list, list):
                    task_runs.extend(task_list)
            return task_runs
            
    # 2. Check detailed_results_by_split directly at root
    detailed = log_data.get("detailed_results_by_split")
    if isinstance(detailed, dict):
        for split, task_list in detailed.items():
            if isinstance(task_list, list):
                task_runs.extend(task_list)
        return task_runs
        
    # 3. Check inside results array (list of trial runs containing detailed_results_by_split)
    results_list = log_data.get("results")
    if isinstance(results_list, list):
        for run_item in results_list:
            if isinstance(run_item, dict):
                det = run_item.get("detailed_results_by_split")
                if isinstance(det, dict):
                    for split, task_list in det.items():
                        if isinstance(task_list, list):
                            task_runs.extend(task_list)
        if task_runs:
            return task_runs
            
    # 4. Check if log_data itself is a single task run
    if "trajectory" in log_data or "traj" in log_data:
        return [log_data]
        
    return []


def extract_successful_trajectories(log_file_path, min_reward=0.99, wiki_raw_text=None):
    """Read a log file and extract successful trajectories."""
    print(f"Reading log file: {log_file_path}")
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)
    except Exception as e:
        print(f"Error reading {log_file_path}: {e}")
        return []
        
    results = get_task_runs(log_data)
            
    samples = []
    success_count = 0
    total_count = 0
    
    # Initialize base tools info
    base_tools_info = [t.get_info() for t in ALL_TOOLS] if ALL_TOOLS else []
    
    for r in results:
        total_count += 1
        reward = r.get("reward", 0.0)
        # Check success
        if reward < min_reward:
            continue
            
        success_count += 1
        task_info = r.get("task", {})
        context_init_config = task_info.get("context_init_config", {})
        removed_part = task_info.get("removed_part", None)
        trajectory = r.get("trajectory", [])
        if not trajectory and "traj" in r:
            trajectory = r.get("traj", [])
            
        # 1. Reconstruct system prompt
        system_prompt = reconstruct_system_prompt(context_init_config)
        
        # 2. Filter tools (remove planning tools + test-specific removals)
        tools_info = remove_tool_elements(base_tools_info, base_tools_info, ["planning_tool", "think"])
        if removed_part:
            tools_info = remove_tool_elements(tools_info, base_tools_info, removed_part)
            
        # 3. Construct message list
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in trajectory:
            if msg.get("role") == "system":
                continue
            
            turn = {
                "role": msg.get("role"),
                "content": msg.get("content")
            }
            if msg.get("tool_calls"):
                turn["tool_calls"] = msg.get("tool_calls")
            if msg.get("tool_call_id"):
                turn["tool_call_id"] = msg.get("tool_call_id")
            if msg.get("name"):
                turn["name"] = msg.get("name")
                
            messages.append(turn)
            
        samples.append({
            "task_id": r.get("task_id"),
            "split": task_info.get("task_type", "unknown"),
            "messages": messages,
            "tools": tools_info
        })
        
    print(f"Extracted {success_count}/{total_count} trajectories (reward >= {min_reward}) from {log_file_path}")
    return samples


def main():
    parser = argparse.ArgumentParser(description="Extract CAR-bench trajectories for SFT.")
    parser.add_argument("--input-path", type=str, default="output",
                        help="Path to evaluator log JSON file, or a directory containing them")
    parser.add_argument("--output-file", type=str, default="data/ft_dataset.jsonl",
                        help="Path to save the extracted JSONL dataset")
    parser.add_argument("--min-reward", type=float, default=0.99,
                        help="Minimum reward threshold to extract trajectories (default: 0.99)")
    args = parser.parse_args()
    
    # Resolve input paths
    log_files = []
    if os.path.isdir(args.input_path):
        log_files = glob.glob(os.path.join(args.input_path, "**/*.json"), recursive=True)
    elif os.path.isfile(args.input_path):
        log_files = [args.input_path]
    else:
        # Try glob pattern
        log_files = glob.glob(args.input_path, recursive=True)
        
    if not log_files:
        print(f"No JSON log files found matching path: {args.input_path}")
        return
        
    print(f"Found {len(log_files)} log file(s) to process.")
    
    all_samples = []
    for log_file in log_files:
        # Skip standard scenario config files if they end up here
        if "scenario" in os.path.basename(log_file) or os.path.basename(log_file) in ["pyproject.toml", "package.json"]:
            continue
        all_samples.extend(extract_successful_trajectories(log_file, min_reward=args.min_reward))
        
    if not all_samples:
        print("No successful trajectories were extracted. No dataset created.")
        return
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    
    # Write to JSONL
    with open(args.output_file, "w", encoding="utf-8") as f:
        for sample in all_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            
    print(f"Saved {len(all_samples)} training samples to {args.output_file}")


if __name__ == "__main__":
    main()
