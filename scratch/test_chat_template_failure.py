import pandas as pd
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer
import json
import sys

print("Loading Qwen 3.5 4B tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3.5-4B", trust_remote_code=True)

print("Loading dataset...")
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
            # If tool_calls was stored as a JSON string instead of parsed list
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
                        
                        # Normalize non-standard `{"name": "...", "arguments": "..."}` to standard format
                        if "name" in call and "arguments" in call and "function" not in call:
                            name = call["name"]
                            args = call["arguments"]
                            # --- QWEN 3.5 4B EXPECTS ARGUMENTS TO BE DICT, NOT STRING ---
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
                            # --- QWEN 3.5 4B EXPECTS ARGUMENTS TO BE DICT, NOT STRING ---
                            if "arguments" in func and isinstance(func["arguments"], str):
                                try:
                                    func["arguments"] = json.loads(func["arguments"])
                                except Exception:
                                    pass
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

# Test row by row
print("Testing Qwen 3.5 4B apply_chat_template row by row...")
for idx, row in full_df.iterrows():
    tools = row.get("tools")
    if not isinstance(tools, list) or len(tools) == 0:
        tools = None
        
    messages = row.get("augmented_messages")
    messages = clean_messages(messages, row_idx=idx)
    
    # Skip empty conversations
    if len(messages) == 0:
        continue
        
    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
            tools=tools
        )
    except Exception as e:
        print(f"\n❌ Failure detected at row index: {idx}")
        print("Tools value:", tools)
        print("Messages value:", messages)
        print("Exception message:", str(e))
        sys.exit(1)

print("🎉 Success! All rows processed successfully without errors!")
