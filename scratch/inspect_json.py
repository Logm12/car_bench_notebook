import json

with open("qwen_custom_sft_full_samples.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = data.get("results", [])
out = []
if len(results) >= 4:
    r = results[3]
    out.append("--- Result 3 ---")
    out.append("Keys: " + str(list(r.keys())))
    out.append("Score: " + str(r.get("score")))
    out.append("Pass rate: " + str(r.get("pass_rate")))
    
    det = r.get("detailed_results_by_split", {})
    out.append("Splits in detailed_results: " + str(list(det.keys())))
    for split, tasks in det.items():
        out.append(f"  Split '{split}': type={type(tasks)}, length={len(tasks)}")
        if isinstance(tasks, list) and len(tasks) > 0:
            out.append(f"    First task: {tasks[0]}")
        elif isinstance(tasks, dict) and len(tasks) > 0:
            first_key = list(tasks.keys())[0]
            out.append(f"    First task ({first_key}): {tasks[first_key]}")

with open("scratch/inspect_output_result3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
