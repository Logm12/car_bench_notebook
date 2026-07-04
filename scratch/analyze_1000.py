import pandas as pd
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer
import json

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3.5-4B", trust_remote_code=True)

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
        if "tool_calls" in msg:
            tc = msg["tool_calls"]
            if isinstance(tc, str):
                try: tc = json.loads(tc)
                except Exception: tc = None
            if isinstance(tc, list):
                cleaned_tc = []
                for tc_idx, call in enumerate(tc):
                    if isinstance(call, dict):
                        call = call.copy()
                        if "name" in call and "arguments" in call and "function" not in call:
                            name = call["name"]
                            args = call["arguments"]
                            if isinstance(args, str):
                                try: args = json.loads(args)
                                except Exception: pass
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
                            if "arguments" in func and isinstance(func["arguments"], str):
                                try: func["arguments"] = json.loads(func["arguments"])
                                except Exception: pass
                            call["function"] = func
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

lengths = []
for idx, row in full_df.head(1000).iterrows():
    tools = row.get("tools")
    if not isinstance(tools, list) or len(tools) == 0:
        tools = None
        
    messages = row.get("augmented_messages")
    messages = clean_messages(messages, row_idx=idx)
    if len(messages) == 0:
        lengths.append(0)
        continue
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
        tools=tools
    )
    lengths.append(len(tokenizer.encode(text)))

import numpy as np
print("Distribution for 1000 rows:")
print("Min:", np.min(lengths))
print("Max:", np.max(lengths))
print("Mean:", np.mean(lengths))
print("Median:", np.median(lengths))
print("Percentiles:")
for p in [5, 10, 25, 50, 75, 90, 95, 99]:
    print(f"{p}th percentile: {np.percentile(lengths, p)}")
