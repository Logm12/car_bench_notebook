import pandas as pd
from huggingface_hub import hf_hub_download
import json

jsonl_files = [
    "data/interactive_agent_disambiguation.jsonl",
    "data/interactive_agent_hallucination.jsonl",
    "data/search_disambiguation.jsonl",
    "data/search_hallucination.jsonl"
]
dfs = []
for filename in jsonl_files:
    local_file_path = hf_hub_download(
        repo_id="upwitu/trash_draft_am",
        filename=filename,
        repo_type="dataset"
    )
    dfs.append(pd.read_json(local_file_path, lines=True))

full_df = pd.concat(dfs, ignore_index=True)

row = full_df.iloc[288]
messages = row.get("augmented_messages")

print("Raw messages at row 288:")
print(messages)

# Let's run clean_messages step-by-step
def clean_messages(messages, row_idx=0):
    if not isinstance(messages, list):
        return []
    
    cleaned = []
    for msg_idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            continue
        msg = msg.copy()
        
        # Normalize tool_calls format if present
        if "tool_calls" in msg:
            tc = msg["tool_calls"]
            print(f"\nMsg {msg_idx} has tool_calls of type {type(tc)}: {tc}")
            if isinstance(tc, str):
                try:
                    tc = json.loads(tc)
                except Exception:
                    tc = None
            
            if isinstance(tc, list):
                cleaned_tc = []
                for tc_idx, call in enumerate(tc):
                    if isinstance(call, dict):
                        call = call.copy()
                        print(f"Call {tc_idx} type: {type(call)}, Keys: {list(call.keys())}")
                        
                        # Normalize non-standard `{"name": "...", "arguments": "..."}` to standard format
                        if "name" in call and "arguments" in call and "function" not in call:
                            name = call["name"]
                            args = call["arguments"]
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except Exception:
                                    pass
                            call = {
                                "id": f"call_{row_idx}_{msg_idx}_{tc_idx}",
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": args
                                }
                            }
                        elif "function" in call and isinstance(call["function"], dict):
                            func = call["function"].copy()
                            print(f"func['arguments'] type before: {type(func.get('arguments'))}, Value: {func.get('arguments')}")
                            # Decode string to dict if needed for Qwen template compatibility
                            if "arguments" in func and isinstance(func["arguments"], str):
                                try:
                                    func["arguments"] = json.loads(func["arguments"])
                                    print("Successfully loaded arguments as json!")
                                except Exception as e:
                                    print("Failed to loads arguments:", str(e))
                            call["function"] = func
                            
                            # Ensure id and type exist in standard format
                            if "id" not in call:
                                call["id"] = f"call_{row_idx}_{msg_idx}_{tc_idx}"
                            if "type" not in call:
                                call["type"] = "function"
                                
                        cleaned_tc.append(call)
                msg["tool_calls"] = cleaned_tc
            else:
                msg.pop("tool_calls", None)
                
        cleaned.append(msg)
    return cleaned

cleaned_msgs = clean_messages(messages, 288)
print("\nCleaned messages:")
print(cleaned_msgs)
