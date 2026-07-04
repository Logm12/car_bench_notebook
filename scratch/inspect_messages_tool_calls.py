import pandas as pd
from huggingface_hub import hf_hub_download

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

# Iterate over messages and inspect tool_calls
for idx, row in full_df.iterrows():
    messages = row.get("augmented_messages")
    if isinstance(messages, list):
        for msg_idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                print(f"Row {idx}, Msg {msg_idx}: not a dict: {type(msg)}")
                continue
            
            tool_calls = msg.get("tool_calls")
            if tool_calls is not None:
                if not isinstance(tool_calls, list):
                    print(f"Row {idx}, Msg {msg_idx}: tool_calls is not a list: {type(tool_calls)}, Value: {tool_calls}")
                    continue
                
                for tc_idx, tc in enumerate(tool_calls):
                    if not isinstance(tc, dict):
                        print(f"Row {idx}, Msg {msg_idx}, TC {tc_idx}: tool_call is not a dict: {type(tc)}")
                        continue
                    
                    # Inspect 'function' in tool_call
                    func = tc.get("function")
                    if func is None:
                        print(f"Row {idx}, Msg {msg_idx}, TC {tc_idx}: tool_call has no 'function' key! Keys: {list(tc.keys())}")
                        continue
                    if not isinstance(func, dict):
                        print(f"Row {idx}, Msg {msg_idx}, TC {tc_idx}: 'function' is not a dict: {type(func)}, Value: {func}")
                        continue
                    
                    # Inspect 'arguments' in function
                    args = func.get("arguments")
                    # In HF/OpenAI, arguments is a string (e.g. '{"city": "Paris"}').
                    # In some datasets, it might be a dictionary!
                    # Wait! In Qwen's chat template, does it try to call .items() on arguments if it's a string, or does it try to parse it?
                    # Let's check!

print("Finished inspecting messages tool calls.")
