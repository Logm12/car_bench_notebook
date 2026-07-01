import json
import os
from collections import Counter

data_dir = "data"
files = {
    "base_train": "raw_tasks_base_train.jsonl",
    "base_test": "raw_tasks_base_test.jsonl",
    "disambiguation_train": "raw_tasks_disambiguation_train.jsonl",
    "disambiguation_test": "raw_tasks_disambiguation_test.jsonl",
    "hallucination_train": "raw_tasks_hallucination_train.jsonl",
    "hallucination_test": "raw_tasks_hallucination_test.jsonl",
}

def analyze_file(file_path):
    total = 0
    task_types = Counter()
    disambig_elements_internal = Counter()
    disambig_elements_user = Counter()
    removed_parts = Counter()
    groundtruth_tools = Counter()
    user_pref_categories_used = Counter()

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            total += 1
            data = json.loads(line)
            
            # Task type
            task_types[data.get("task_type", "unknown")] += 1
            
            # Disambiguation elements
            if data.get("disambiguation_element_internal"):
                disambig_elements_internal[data.get("disambiguation_element_internal")] += 1
            if data.get("disambiguation_element_user"):
                disambig_elements_user[data.get("disambiguation_element_user")] += 1
                
            # Removed parts (for hallucination tasks)
            rm_parts = data.get("removed_part")
            if rm_parts:
                if isinstance(rm_parts, list):
                    for p in rm_parts:
                        removed_parts[p] += 1
                else:
                    removed_parts[rm_parts] += 1
            
            # Groundtruth actions/tools
            actions_str = data.get("actions", "[]")
            try:
                actions = json.loads(actions_str)
                for act in actions:
                    groundtruth_tools[act.get("name", "unknown")] += 1
            except Exception:
                pass
                
            # Stored user preferences in context init
            ctx_init_str = data.get("context_init_config", "{}")
            try:
                ctx_init = json.loads(ctx_init_str)
                prefs = ctx_init.get("user_preferences", {})
                for cat, subcat_dict in prefs.items():
                    # check if any category has content
                    has_content = False
                    if isinstance(subcat_dict, list) and len(subcat_dict) > 0:
                        has_content = True
                    elif isinstance(subcat_dict, dict):
                        for subk, subv in subcat_dict.items():
                            if subv:
                                has_content = True
                    if has_content:
                        user_pref_categories_used[cat] += 1
            except Exception:
                pass

    return {
        "total": total,
        "task_types": dict(task_types),
        "disambig_elements_internal": dict(disambig_elements_internal),
        "disambig_elements_user": dict(disambig_elements_user),
        "removed_parts": dict(removed_parts),
        "groundtruth_tools": dict(groundtruth_tools),
        "user_pref_categories_used": dict(user_pref_categories_used),
    }

results = {}
for key, filename in files.items():
    path = os.path.join(data_dir, filename)
    analysis = analyze_file(path)
    if analysis:
        results[key] = analysis

# Print structured summary
print("=== DETAILED DATASET ANALYSIS ===")
for key, res in results.items():
    print(f"\n>>> Split: {key} (Total: {res['total']} tasks)")
    print(f"  Task Types: {res['task_types']}")
    
    if res['disambig_elements_internal']:
        print(f"  Internal Disambiguation Targets (Top 5): {sorted(res['disambig_elements_internal'].items(), key=lambda x: x[1], reverse=True)[:5]}")
    if res['disambig_elements_user']:
        print(f"  User Disambiguation Targets (Top 5): {sorted(res['disambig_elements_user'].items(), key=lambda x: x[1], reverse=True)[:5]}")
        
    if res['removed_parts']:
        print(f"  Removed Tools/Parameters (Top 5): {sorted(res['removed_parts'].items(), key=lambda x: x[1], reverse=True)[:5]}")
        
    print(f"  Top 5 Groundtruth Tools Called: {sorted(res['groundtruth_tools'].items(), key=lambda x: x[1], reverse=True)[:5]}")
    print(f"  Active User Preference Categories: {res['user_pref_categories_used']}")
