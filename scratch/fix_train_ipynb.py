import json
import os

ipynb_path = "e:/VinAI/VSG/car-bench-ijcai-vsf/llm-training/train.ipynb"

if not os.path.exists(ipynb_path):
    print(f"Error: {ipynb_path} not found.")
    exit(1)

with open(ipynb_path, "r", encoding="utf-8") as f:
    notebook = json.load(f)

# Code mới để thay thế
new_source = [
    "from huggingface_hub import hf_hub_download\n",
    "import pandas as pd\n",
    "from datasets import Dataset\n",
    "\n",
    "print(\"Downloading dataset raw jsonl files directly to bypass metadata validation issues...\")\n",
    "jsonl_files = [\n",
    "    \"data/interactive_agent_disambiguation.jsonl\",\n",
    "    \"data/interactive_agent_hallucination.jsonl\",\n",
    "    \"data/search_disambiguation.jsonl\",\n",
    "    \"data/search_hallucination.jsonl\"\n",
    "]\n",
    "\n",
    "dfs = []\n",
    "for filename in jsonl_files:\n",
    "    print(f\"Downloading {filename} from HF Hub...\")\n",
    "    local_file_path = hf_hub_download(\n",
    "        repo_id=\"upwitu/trash_draft_am\",\n",
    "        filename=filename,\n",
    "        repo_type=\"dataset\"\n",
    "    )\n",
    "    dfs.append(pd.read_json(local_file_path, lines=True))\n",
    "\n",
    "print(\"Concatenating splits into a single DataFrame...\")\n",
    "full_df = pd.concat(dfs, ignore_index=True)\n",
    "print(f\"Combined dataset size: {len(full_df)}\")\n",
    "\n",
    "# Convert to HF Dataset\n",
    "dataset = Dataset.from_pandas(full_df)\n",
    "print(f\"Dataset successfully loaded and parsed! Total size: {len(dataset)}\")"
]

updated = False
# Tìm cell chứa dòng load_dataset("upwitu/trash_draft_am"
for cell in notebook.get("cells", []):
    if cell.get("cell_type") == "code":
        source_text = "".join(cell.get("source", []))
        if 'load_dataset("upwitu/trash_draft_am"' in source_text or 'load_dataset(\"upwitu/trash_draft_am\"' in source_text:
            cell["source"] = new_source
            updated = True
            print("Successfully updated load_dataset cell in train.ipynb!")
            break

if not updated:
    # Nếu không tìm thấy bằng regex chính xác, chèn một cell mới ở vị trí thích hợp hoặc báo cho người dùng
    print("Could not find the exact load_dataset cell. Checking list for any load_dataset...")
    for idx, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") == "code":
            source_text = "".join(cell.get("source", []))
            if "load_dataset" in source_text and "upwitu" in source_text:
                cell["source"] = new_source
                updated = True
                print(f"Updated cell {idx} containing load_dataset and upwitu!")
                break

if updated:
    with open(ipynb_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)
    print("Notebook train.ipynb successfully saved.")
else:
    print("No cell matching dataset loading was found.")
