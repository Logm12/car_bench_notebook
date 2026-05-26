import json
import os
import re

notebooks = {
    "notebooks/qwen_coder_baseline.ipynb": {
        "insert_before": "## 3. Local vLLM Inference Server",
        "new_section_num": 3,
        "new_title": "## 3. Dataset Download & Exploration",
        "desc": "We download the official CAR-bench dataset from Hugging Face at [johanneskirmayr/car-bench-dataset](https://huggingface.co/datasets/johanneskirmayr/car-bench-dataset) to verify and cache the training/validation data splits locally."
    },
    "notebooks/finetune_llm.ipynb": {
        "insert_before": "## 3. Data Preparation",
        "new_section_num": 3,
        "new_title": "## 3. Dataset Download & Exploration",
        "desc": "We download the official CAR-bench dataset from Hugging Face at [johanneskirmayr/car-bench-dataset](https://huggingface.co/datasets/johanneskirmayr/car-bench-dataset) to cache the training and validation splits locally before preprocessing."
    },
    "notebooks/finetune_llm_dpo.ipynb": {
        "insert_before": "## 3. LLM Rejected Preference Pair Generator",
        "new_section_num": 3,
        "new_title": "## 3. Dataset Download & Exploration",
        "desc": "We download the official CAR-bench dataset from Hugging Face at [johanneskirmayr/car-bench-dataset](https://huggingface.co/datasets/johanneskirmayr/car-bench-dataset) to cache the training and validation splits locally before SFT/DPO alignment."
    }
}

download_code = [
    "from datasets import load_dataset\n",
    "import os\n",
    "\n",
    "print(\"Downloading CAR-bench dataset from Hugging Face (johanneskirmayr/car-bench-dataset)...\")\n",
    "configs = [\"tasks_base\", \"tasks_disambiguation\", \"tasks_hallucination\"]\n",
    "splits = [\"train\", \"test\"]\n",
    "\n",
    "os.makedirs(\"data\", exist_ok=True)\n",
    "\n",
    "for config in configs:\n",
    "    for split in splits:\n",
    "        print(f\"Downloading split: config={config}, split={split}...\")\n",
    "        ds = load_dataset(\"johanneskirmayr/car-bench-dataset\", config, split=split)\n",
    "        print(f\"  Successfully loaded {len(ds)} samples.\")\n",
    "        \n",
    "        # Save raw dataset copy locally for verification and exploration\n",
    "        raw_path = f\"data/raw_{config}_{split}.jsonl\"\n",
    "        ds.to_json(raw_path)\n",
    "        print(f\"  Saved locally to: {raw_path}\")\n"
]

for nb_path, config in notebooks.items():
    if not os.path.exists(nb_path):
        print(f"File not found: {nb_path}")
        continue
        
    print(f"Updating: {nb_path}")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
        
    # Find insert index
    insert_idx = -1
    for idx, cell in enumerate(nb_data["cells"]):
        if cell["cell_type"] == "markdown" and cell["source"]:
            first_line = cell["source"][0].strip()
            if first_line == config["insert_before"]:
                insert_idx = idx
                break
                
    if insert_idx == -1:
        print(f"Could not find cell: {config['insert_before']} in {nb_path}")
        continue
        
    # Increment all subsequent header numbers by 1
    header_pattern = re.compile(r"^##\s+(\d+)\.\s+(.*)$")
    for cell in nb_data["cells"]:
        if cell["cell_type"] == "markdown" and cell["source"]:
            first_line = cell["source"][0]
            match = header_pattern.match(first_line.strip())
            if match:
                num = int(match.group(1))
                if num >= config["new_section_num"]:
                    new_num = num + 1
                    cell["source"][0] = f"## {new_num}. {match.group(2)}\n"
                    # Also update formatting in subsequent lines of the same cell if any
                    for i in range(1, len(cell["source"])):
                        line = cell["source"][i]
                        cell["source"][i] = re.sub(rf"^##\s+{num}\.", f"## {new_num}.", line)
                        
    # Insert new cells
    new_md_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            f"{config['new_title']}\n",
            "\n",
            f"{config['desc']}\n"
        ]
    }
    
    new_code_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": download_code
    }
    
    nb_data["cells"].insert(insert_idx, new_md_cell)
    nb_data["cells"].insert(insert_idx + 1, new_code_cell)
    
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, indent=1, ensure_ascii=False)
        f.write("\n")
        
    print(f"Successfully updated {nb_path}")
