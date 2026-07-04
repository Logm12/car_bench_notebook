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

# Iterate over tools and inspect structure
for idx, row in full_df.iterrows():
    tools = row.get("tools")
    if isinstance(tools, list) and len(tools) > 0:
        for tool_idx, tool in enumerate(tools):
            if not isinstance(tool, dict):
                print(f"Row {idx}, Tool {tool_idx}: not a dict: {type(tool)}")
                continue
            
            # Check function mapping
            func = tool.get("function")
            if func is None:
                # Some templates expect 'function' key, what if it's named something else or missing?
                print(f"Row {idx}, Tool {tool_idx}: no 'function' key! Keys: {list(tool.keys())}")
                continue
                
            if not isinstance(func, dict):
                print(f"Row {idx}, Tool {tool_idx}: 'function' is not a dict: {type(func)}")
                continue
                
            # Check parameters mapping
            params = func.get("parameters")
            if params is not None:
                if not isinstance(params, dict):
                    print(f"Row {idx}, Tool {tool_idx}: 'parameters' is not a dict: {type(params)}")
                    continue
                
                # Check properties mapping
                props = params.get("properties")
                if props is not None:
                    if not isinstance(props, dict):
                        print(f"Row {idx}, Tool {tool_idx}: 'properties' is not a dict: {type(props)}")
                        continue
                else:
                    # Properties is missing
                    pass

print("Finished inspecting tools details.")
