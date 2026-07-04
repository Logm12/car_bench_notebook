import json
import os
import sys

# Search in both root and output directories
json_paths = ["qwen_custom_sft_full_samples.json", "output/qwen_custom_sft_full_samples.json"]
json_path = None
for path in json_paths:
    if os.path.exists(path):
        json_path = path
        break

if not json_path:
    print(f"Error: qwen_custom_sft_full_samples.json not found in search paths {json_paths}.")
    sys.exit(1)

md_path = "evaluation_report.md"
if os.path.exists("output"):
    md_path = "output/evaluation_report.md"

print(f"Reading evaluation results from {json_path}...")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Get results list
results_list = data.get("results", [])
if not results_list:
    print("Error: No 'results' key found in JSON.")
    sys.exit(1)

# Parse the latest result block
latest_result = results_list[-1]
pass_rate = latest_result.get("pass_rate", 0.0)
if pass_rate <= 1.0:
    pass_rate *= 100

detailed_results = latest_result.get("detailed_results_by_split", {})

all_tasks = []
split_stats = {}

for split, tasks_list in detailed_results.items():
    if split not in split_stats:
        split_stats[split] = {"total": 0, "success": 0, "steps": []}
        
    for task_data in tasks_list:
        task_id = task_data.get("task_id")
        reward = task_data.get("reward", 0.0)
        success = (reward == 1.0)
        
        # Calculate steps by counting assistant turns in trajectory
        trajectory = task_data.get("trajectory", [])
        steps = sum(1 for turn in trajectory if turn.get("role") == "assistant")
        
        task_info = {
            "task_id": task_id,
            "split": split,
            "success": success,
            "steps": steps,
            "reward": reward
        }
        all_tasks.append(task_info)
        
        split_stats[split]["total"] += 1
        if success:
            split_stats[split]["success"] += 1
        split_stats[split]["steps"].append(steps)

total_tasks = len(all_tasks)
succeeded_tasks = sum(1 for t in all_tasks if t["success"])
failed_tasks = total_tasks - succeeded_tasks

# Generate Markdown content
md_content = f"""# CAR-bench Evaluation Report

This report summarizes the performance of the fine-tuned **Qwen3.5-4B SFT** model evaluated on the official CAR-bench test split.

## 1. Executive Summary

| Metric | Value |
|---|---|
| **Model** | Qwen3.5-4B-SFT |
| **Dataset Split** | test |
| **Overall Pass Rate** | **{pass_rate:.2f}%** |
| **Total Evaluation Tasks** | {total_tasks} |
| **Successful Tasks** | {succeeded_tasks} |
| **Failed Tasks** | {failed_tasks} |

---

## 2. Performance by Task Split

| Split | Total Tasks | Successful | Pass Rate | Avg Steps |
|---|---|---|---|---|
"""

for split, stats in split_stats.items():
    s_total = stats["total"]
    s_succ = stats["success"]
    s_rate = (s_succ / s_total) * 100 if s_total > 0 else 0
    avg_steps = sum(stats["steps"]) / len(stats["steps"]) if stats["steps"] else 0
    md_content += f"| **{split.capitalize()}** | {s_total} | {s_succ} | {s_rate:.2f}% | {avg_steps:.1f} |\n"

md_content += """
---

## 3. Failed Tasks Analysis

Below is the list of tasks that failed during the evaluation. These edge cases are prime candidates for preference-tuning (DPO/ORPO).

| Task ID | Split | Steps | Final Reward |
|---|---|---|---|
"""

failures = [t for t in all_tasks if not t["success"]]
if failures:
    for fail in failures:
        md_content += f"| `{fail['task_id']}` | {fail['split']} | {fail['steps']} | {fail['reward']:.2f} |\n"
else:
    md_content += "| *None! All tasks passed successfully.* | | | |\n"

md_content += """
---

## 4. Full Task Results

<details>
<summary>Click to view the full list of evaluated tasks</summary>

| Task ID | Split | Status | Steps | Reward |
|---|---|---|---|---|
"""

for trial in all_tasks:
    status = "✅ Success" if trial["success"] else "❌ Fail"
    md_content += f"| `{trial['task_id']}` | {trial['split']} | {status} | {trial['steps']} | {trial['reward']:.2f} |\n"

md_content += """
</details>

---

## 5. Next Steps / Insights
1. **Analyze Failure Scenarios:** Open the result JSON and search for the specific `task_id` listed in Section 3 to see the conversation history and find where the model went wrong.
2. **Preference Alignment (DPO/ORPO):** Use the failed trajectories to build a preference dataset (chosen vs rejected) to perform Stage 2 RLHF alignment on the model.
"""

with open(md_path, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"Report successfully written to: {md_path}")
