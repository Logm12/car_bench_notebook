import json
import os

def update_orpo_notebook(filepath):
    print(f"Updating {filepath}...")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # 1. Update git clone command to BTC repo
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and any('!git clone' in line for line in cell['source']):
            new_source = []
            for line in cell['source']:
                if '!git clone' in line:
                    line = line.replace("https://github.com/VinAI-Research/car-bench-ijcai-vsf.git", "https://github.com/Logm12/car-bench-ijcai-vsf")
                    line = line.replace("car-bench-ijcai-vsf.git", "car-bench-ijcai-vsf")
                new_source.append(line)
            cell['source'] = new_source
            print("  Updated git clone command.")
            break

    # 2. Update first imports cell to import unsloth before transformers/trl to avoid UserWarning
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and any('import torch' in line for line in cell['source']) and any('import random' in line for line in cell['source']):
            cell['source'] = [
                "# Restructure imports: Unsloth must be imported before any transformers/trl/peft libraries\n",
                "try:\n",
                "    from unsloth import FastLanguageModel\n",
                "except ImportError:\n",
                "    pass\n",
                "\n",
                "import os\n",
                "import sys\n",
                "import json\n",
                "import torch\n",
                "import random\n",
                "\n",
                "# Establish seeds for training reproducibility\n",
                "random.seed(42)\n",
                "torch.manual_seed(42)\n",
                "if torch.cuda.is_available():\n",
                "    torch.cuda.manual_seed_all(42)"
            ]
            print("  Restructured first imports cell.")
            break

    # 3. Replace dataset loading block to support mapping and caching (to disk)
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and any('Local data not available. Loading and preparing tasks' in line for line in cell['source']):
            cell['source'] = [
                "import os\n",
                "import json\n",
                "from datasets import Dataset, load_dataset\n",
                "\n",
                "# Configuration paths\n",
                "local_mapped_path = \"data/dpo_dataset_hf_mapped.jsonl\"\n",
                "os.makedirs(\"data\", exist_ok=True)\n",
                "\n",
                "dataset = None\n",
                "\n",
                "# Step 1: Check if already preprocessed and cached on disk to prevent loss on OOM/crash\n",
                "if os.path.exists(local_mapped_path):\n",
                "    print(f\"Loading cached preprocessed dataset from {local_mapped_path}...\")\n",
                "    try:\n",
                "        dataset = load_dataset(\"json\", data_files=local_mapped_path, split=\"train\")\n",
                "    except Exception as e:\n",
                "        print(f\"Error loading cached dataset: {e}\")\n",
                "\n",
                "# Step 2: Fallback to local logs parse if available\n",
                "if not dataset or len(dataset) == 0:\n",
                "    dpo_dataset_path = \"data/dpo_dataset.jsonl\"\n",
                "    if os.path.exists(dpo_dataset_path):\n",
                "        print(f\"Loading local preference dataset from {dpo_dataset_path}...\")\n",
                "        try:\n",
                "            dataset = load_dataset(\"json\", data_files=dpo_dataset_path, split=\"train\")\n",
                "        except Exception as e:\n",
                "            print(f\"Error loading local json dataset: {e}\")\n",
                "\n",
                "# Step 3: Fallback to Hugging Face dataset download + preprocessing mapping + caching\n",
                "if not dataset or len(dataset) == 0:\n",
                "    print(\"Preprocessed cached dataset not found. Downloading and preprocessing from Hugging Face johanneskirmayr/car-bench-dataset...\")\n",
                "    try:\n",
                "        from datasets import load_dataset as hf_load_dataset\n",
                "        import random\n",
                "        from openai import OpenAI\n",
                "        \n",
                "        splits = [\"tasks_base\", \"tasks_disambiguation\", \"tasks_hallucination\"]\n",
                "        dpo_samples = []\n",
                "        \n",
                "        # Load environment API Key\n",
                "        api_key = os.environ.get(\"OPENAI_API_KEY\")\n",
                "        client = OpenAI(api_key=api_key) if api_key else None\n",
                "        if not client:\n",
                "            print(\"OPENAI_API_KEY not set. Falling back to heuristic mutations for negative examples.\")\n",
                "            \n",
                "        wiki_file = \"third_party/car-bench/car_bench/envs/car_voice_assistant/wiki.md\"\n",
                "        if not os.path.exists(wiki_file):\n",
                "            wiki_file = \"car-bench-ijcai-vsf/third_party/car-bench/car_bench/envs/car_voice_assistant/wiki.md\"\n",
                "        \n",
                "        wiki_raw = \"\"\n",
                "        if os.path.exists(wiki_file):\n",
                "            with open(wiki_file, \"r\", encoding=\"utf-8\") as f:\n",
                "                wiki_raw = f.read()\n",
                "                \n",
                "        for config_name in splits:\n",
                "            for split_name in [\"train\", \"test\"]:\n",
                "                try:\n",
                "                    print(f\"Loading and mapping Hugging Face split: {config_name} ({split_name})...\")\n",
                "                    ds = hf_load_dataset(\"johanneskirmayr/car-bench-dataset\", config_name, split=split_name)\n",
                "                    for item in ds:\n",
                "                        instruction = item.get(\"instruction\", \"\")\n",
                "                        context_init = item.get(\"context_init_config\", \"{}\")\n",
                "                        if isinstance(context_init, str):\n",
                "                            try:\n",
                "                                context_init_data = json.loads(context_init)\n",
                "                            except Exception:\n",
                "                                context_init_data = {}\n",
                "                        else:\n",
                "                            context_init_data = context_init\n",
                "                            \n",
                "                        # Build system prompt with context placeholders replaced\n",
                "                        if wiki_raw:\n",
                "                            location_str = json.dumps(context_init_data.get(\"current_location\", {}), separators=(',', ':'))\n",
                "                            datetime_str = json.dumps(context_init_data.get(\"current_datetime\", {}), separators=(',', ':'))\n",
                "                            system_prompt = wiki_raw.replace(\"INS:\", \"\").replace(\"AUT-POL:\", \"\").replace(\"LLM-POL:\", \"\")\n",
                "                            system_prompt = system_prompt.replace(\"{{placeholder_location_based_on_task_context_init_config}}\", location_str)\n",
                "                            system_prompt = system_prompt.replace(\"{{placeholder_datetime_based_on_task_context_init_config}}\", datetime_str)\n",
                "                        else:\n",
                "                            system_prompt = \"You are a helpful in-car voice assistant.\"\n",
                "                            \n",
                "                        actions_str = item.get(\"actions\", \"[]\")\n",
                "                        chosen_content = f\"Thought: I need to execute the following actions.\\n{actions_str}\"\n",
                "                        \n",
                "                        prompt_history = [\n",
                "                            {\"role\": \"system\", \"content\": system_prompt},\n",
                "                            {\"role\": \"user\", \"content\": instruction}\n",
                "                        ]\n",
                "                        \n",
                "                        # Generate rejected content\n",
                "                        rejected_content = None\n",
                "                        if client:\n",
                "                            rule = random.choice([\n",
                "                                \"Call a tool without getting a prior confirmation from the user (violates user confirmation rule).\",\n",
                "                                \"Call a planning_tool directly (violates forbidden tool rule).\",\n",
                "                                \"Output reasoning thoughts in plaintext rather than JSON (violates output format rule).\",\n",
                "                                \"Return incorrect coordinates or search fields (violates accuracy rule).\"\n",
                "                            ])\n",
                "                            try:\n",
                "                                chat_completion = client.chat.completions.create(\n",
                "                                    model=\"gpt-4o-mini\",\n",
                "                                    messages=[\n",
                "                                        {\"role\": \"system\", \"content\": \"You are a database alignment assistant. Generate a negative example violating the specified rule.\"},\n",
                "                                        {\"role\": \"user\", \"content\": f\"Take the following successful assistant response and rewrite it to violate the rule: {rule}\\n\\nResponse:\\n{chosen_content}\"}\n",
                "                                    ],\n",
                "                                    temperature=0.7,\n",
                "                                    max_tokens=800\n",
                "                                )\n",
                "                                rejected_content = chat_completion.choices[0].message.content.strip()\n",
                "                            except Exception as api_err:\n",
                "                                print(f\"API generation error: {api_err}. Falling back to heuristic mutation.\")\n",
                "                                \n",
                "                        if not rejected_content:\n",
                "                            try:\n",
                "                                actions = json.loads(actions_str)\n",
                "                                if actions:\n",
                "                                    actions[0][\"name\"] = \"planning_tool\"\n",
                "                                rejected_content = f\"Thought: I need to execute the following actions.\\n{json.dumps(actions)}\"\n",
                "                            except Exception:\n",
                "                                rejected_content = f\"Thought: I need to execute the following actions.\\n[]\"\n",
                "                                \n",
                "                        dpo_samples.append({\n",
                "                            \"prompt\": prompt_history,\n",
                "                            \"chosen\": [{\"role\": \"assistant\", \"content\": chosen_content}],\n",
                "                            \"rejected\": [{\"role\": \"assistant\", \"content\": rejected_content}]\n",
                "                        })\n",
                "                except Exception as e:\n",
                "                    print(f\"Skipped HF config {config_name} {split_name}: {e}\")\n",
                "                    \n",
                "        dataset = Dataset.from_list(dpo_samples)\n",
                "        \n",
                "        # Cache the preprocessed dataset immediately to disk to prevent loss on OOM\n",
                "        print(f\"Caching preprocessed preference dataset to {local_mapped_path}...\")\n",
                "        dataset.to_json(local_mapped_path)\n",
                "    except Exception as e:\n",
                "        print(f\"Failed to load dataset from Hugging Face: {e}\")\n",
                "        dataset = Dataset.from_list([])\n",
                "\n",
                "print(f\"Preference dataset loaded. Total samples: {len(dataset)}\")"
            ]
            print("  Updated dataset loading/mapping/caching block.")
            break

    # 4. Add average_tokens_across_devices=False to ORPOConfig to fix AttributeError: 'int' object has no attribute 'mean'
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and 'orpo_config = ORPOConfig(' in ''.join(cell['source']):
            new_source = []
            for line in cell['source']:
                if 'report_to="none"' in line:
                    line = line.replace('report_to="none"', 'report_to="none",\n    average_tokens_across_devices=False')
                new_source.append(line)
            cell['source'] = new_source
            print("  Added average_tokens_across_devices=False to ORPOConfig.")
            break

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("ORPO notebook update completed.")

def update_dpo_notebook(filepath):
    print(f"Updating {filepath}...")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # 1. Update git clone command to BTC repo
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and any('!git clone' in line for line in cell['source']):
            new_source = []
            for line in cell['source']:
                if '!git clone' in line:
                    line = line.replace("https://github.com/VinAI-Research/car-bench-ijcai-vsf.git", "https://github.com/Logm12/car-bench-ijcai-vsf")
                    line = line.replace("car-bench-ijcai-vsf.git", "car-bench-ijcai-vsf")
                new_source.append(line)
            cell['source'] = new_source
            print("  Updated git clone command.")
            break

    # 2. Update first imports cell to import unsloth before transformers/trl to avoid UserWarning
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and any('import torch' in line for line in cell['source']) and any('import random' in line for line in cell['source']):
            cell['source'] = [
                "# Restructure imports: Unsloth must be imported before any transformers/trl/peft libraries\n",
                "try:\n",
                "    from unsloth import FastLanguageModel\n",
                "except ImportError:\n",
                "    pass\n",
                "\n",
                "import os\n",
                "import sys\n",
                "import json\n",
                "import torch\n",
                "import random\n",
                "\n",
                "# Establish seeds for training reproducibility\n",
                "random.seed(42)\n",
                "torch.manual_seed(42)\n",
                "if torch.cuda.is_available():\n",
                "    torch.cuda.manual_seed_all(42)"
            ]
            print("  Restructured first imports cell.")
            break

    # 3. Replace dataset loading cell with mapping + caching block to prevent data loss on OOM
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and any('Local datasets missing or incomplete. Loading and preparing tasks' in line for line in cell['source']):
            cell['source'] = [
                "from datasets import Dataset, load_dataset\n",
                "import os\n",
                "import json\n",
                "\n",
                "local_sft_mapped_path = \"data/sft_dataset_hf_mapped.jsonl\"\n",
                "local_dpo_mapped_path = \"data/dpo_dataset_hf_mapped.jsonl\"\n",
                "os.makedirs(\"data\", exist_ok=True)\n",
                "\n",
                "sft_dataset = None\n",
                "dpo_dataset = None\n",
                "\n",
                "# Step 1: Check if already preprocessed and cached on disk to prevent loss on OOM/crash\n",
                "if os.path.exists(local_sft_mapped_path):\n",
                "    print(f\"Loading cached preprocessed SFT dataset from {local_sft_mapped_path}...\")\n",
                "    try:\n",
                "        sft_dataset = load_dataset(\"json\", data_files=local_sft_mapped_path, split=\"train\")\n",
                "    except Exception as e:\n",
                "        print(f\"Error loading cached SFT dataset: {e}\")\n",
                "\n",
                "if os.path.exists(local_dpo_mapped_path):\n",
                "    print(f\"Loading cached preprocessed DPO dataset from {local_dpo_mapped_path}...\")\n",
                "    try:\n",
                "        dpo_dataset = load_dataset(\"json\", data_files=local_dpo_mapped_path, split=\"train\")\n",
                "    except Exception as e:\n",
                "        print(f\"Error loading cached DPO dataset: {e}\")\n",
                "\n",
                "# Step 2: Fallback to local logs parse if available\n",
                "if not sft_dataset or not dpo_dataset:\n",
                "    sft_dataset_path = \"data/sft_dataset.jsonl\"\n",
                "    dpo_dataset_path = \"data/dpo_dataset.jsonl\"\n",
                "    if os.path.exists(sft_dataset_path) and not sft_dataset:\n",
                "        print(f\"Loading local SFT dataset from {sft_dataset_path}...\")\n",
                "        try:\n",
                "            sft_dataset = load_dataset(\"json\", data_files=sft_dataset_path, split=\"train\")\n",
                "        except Exception as e:\n",
                "            print(f\"Error loading SFT dataset: {e}\")\n",
                "    if os.path.exists(dpo_dataset_path) and not dpo_dataset:\n",
                "        print(f\"Loading local DPO dataset from {dpo_dataset_path}...\")\n",
                "        try:\n",
                "            dpo_dataset = load_dataset(\"json\", data_files=dpo_dataset_path, split=\"train\")\n",
                "        except Exception as e:\n",
                "            print(f\"Error loading DPO dataset: {e}\")\n",
                "\n",
                "# Step 3: Fallback to Hugging Face dataset download + preprocessing mapping + caching\n",
                "if not sft_dataset or not dpo_dataset:\n",
                "    print(\"Preprocessed cached datasets not found. Downloading and preprocessing from Hugging Face johanneskirmayr/car-bench-dataset...\")\n",
                "    try:\n",
                "        from datasets import load_dataset as hf_load_dataset\n",
                "        import random\n",
                "        from openai import OpenAI\n",
                "        \n",
                "        splits = [\"tasks_base\", \"tasks_disambiguation\", \"tasks_hallucination\"]\n",
                "        sft_samples = []\n",
                "        dpo_samples = []\n",
                "        \n",
                "        # Load environment API Key\n",
                "        api_key = os.environ.get(\"OPENAI_API_KEY\")\n",
                "        client = OpenAI(api_key=api_key) if api_key else None\n",
                "        if not client:\n",
                "            print(\"OPENAI_API_KEY not set. Falling back to heuristic mutations for negative examples.\")\n",
                "            \n",
                "        wiki_file = \"third_party/car-bench/car_bench/envs/car_voice_assistant/wiki.md\"\n",
                "        if not os.path.exists(wiki_file):\n",
                "            wiki_file = \"car-bench-ijcai-vsf/third_party/car-bench/car_bench/envs/car_voice_assistant/wiki.md\"\n",
                "        \n",
                "        wiki_raw = \"\"\n",
                "        if os.path.exists(wiki_file):\n",
                "            with open(wiki_file, \"r\", encoding=\"utf-8\") as f:\n",
                "                wiki_raw = f.read()\n",
                "                \n",
                "        for config_name in splits:\n",
                "            for split_name in [\"train\", \"test\"]:\n",
                "                try:\n",
                "                    print(f\"Loading and mapping Hugging Face split: {config_name} ({split_name})...\")\n",
                "                    ds = hf_load_dataset(\"johanneskirmayr/car-bench-dataset\", config_name, split=split_name)\n",
                "                    for item in ds:\n",
                "                        instruction = item.get(\"instruction\", \"\")\n",
                "                        context_init = item.get(\"context_init_config\", \"{}\")\n",
                "                        if isinstance(context_init, str):\n",
                "                            try:\n",
                "                                context_init_data = json.loads(context_init)\n",
                "                            except Exception:\n",
                "                                context_init_data = {}\n",
                "                        else:\n",
                "                            context_init_data = context_init\n",
                "                            \n",
                "                        # Build system prompt with context placeholders replaced\n",
                "                        if wiki_raw:\n",
                "                            location_str = json.dumps(context_init_data.get(\"current_location\", {}), separators=(',', ':'))\n",
                "                            datetime_str = json.dumps(context_init_data.get(\"current_datetime\", {}), separators=(',', ':'))\n",
                "                            system_prompt = wiki_raw.replace(\"INS:\", \"\").replace(\"AUT-POL:\", \"\").replace(\"LLM-POL:\", \"\")\n",
                "                            system_prompt = system_prompt.replace(\"{{placeholder_location_based_on_task_context_init_config}}\", location_str)\n",
                "                            system_prompt = system_prompt.replace(\"{{placeholder_datetime_based_on_task_context_init_config}}\", datetime_str)\n",
                "                        else:\n",
                "                            system_prompt = \"You are a helpful in-car voice assistant.\"\n",
                "                            \n",
                "                        actions_str = item.get(\"actions\", \"[]\")\n",
                "                        chosen_content = f\"Thought: I need to execute the following actions.\\n{actions_str}\"\n",
                "                        \n",
                "                        prompt_history = [\n",
                "                            {\"role\": \"system\", \"content\": system_prompt},\n",
                "                            {\"role\": \"user\", \"content\": instruction}\n",
                "                        ]\n",
                "                        \n",
                "                        # Build SFT sample\n",
                "                        sft_samples.append({\n",
                "                            \"messages\": prompt_history + [{\"role\": \"assistant\", \"content\": chosen_content}]\n",
                "                        })\n",
                "                        \n",
                "                        # Build DPO sample (chosen vs rejected)\n",
                "                        rejected_content = None\n",
                "                        if client:\n",
                "                            rule = random.choice([\n",
                "                                \"Call a tool without getting a prior confirmation from the user (violates user confirmation rule).\",\n",
                "                                \"Call a planning_tool directly (violates forbidden tool rule).\",\n",
                "                                \"Output reasoning thoughts in plaintext rather than JSON (violates output format rule).\",\n",
                "                                \"Return incorrect coordinates or search fields (violates accuracy rule).\"\n",
                "                            ])\n",
                "                            try:\n",
                "                                chat_completion = client.chat.completions.create(\n",
                "                                    model=\"gpt-4o-mini\",\n",
                "                                    messages=[\n",
                "                                        {\"role\": \"system\", \"content\": \"You are a database alignment assistant. Generate a negative example violating the specified rule.\"},\n",
                "                                        {\"role\": \"user\", \"content\": f\"Take the following successful assistant response and rewrite it to violate the rule: {rule}\\n\\nResponse:\\n{chosen_content}\"}\n",
                "                                    ],\n",
                "                                    temperature=0.7,\n",
                "                                    max_tokens=800\n",
                "                                )\n",
                "                                rejected_content = chat_completion.choices[0].message.content.strip()\n",
                "                            except Exception as api_err:\n",
                "                                print(f\"API generation error: {api_err}. Falling back to heuristic mutation.\")\n",
                "                                \n",
                "                        if not rejected_content:\n",
                "                            try:\n",
                "                                actions = json.loads(actions_str)\n",
                "                                if actions:\n",
                "                                    actions[0][\"name\"] = \"planning_tool\"\n",
                "                                rejected_content = f\"Thought: I need to execute the following actions.\\n{json.dumps(actions)}\"\n",
                "                            except Exception:\n",
                "                                rejected_content = f\"Thought: I need to execute the following actions.\\n[]\"\n",
                "                                \n",
                "                        dpo_samples.append({\n",
                "                            \"prompt\": prompt_history,\n",
                "                            \"chosen\": [{\"role\": \"assistant\", \"content\": chosen_content}],\n",
                "                            \"rejected\": [{\"role\": \"assistant\", \"content\": rejected_content}]\n",
                "                        })\n",
                "                except Exception as e:\n",
                "                    print(f\"Skipped HF config {config_name} {split_name}: {e}\")\n",
                "                    \n",
                "        if not sft_dataset:\n",
                "            sft_dataset = Dataset.from_list(sft_samples)\n",
                "            print(f\"Caching SFT dataset to {local_sft_mapped_path}...\")\n",
                "            sft_dataset.to_json(local_sft_mapped_path)\n",
                "            \n",
                "        if not dpo_dataset:\n",
                "            dpo_dataset = Dataset.from_list(dpo_samples)\n",
                "            print(f\"Caching DPO dataset to {local_dpo_mapped_path}...\")\n",
                "            dpo_dataset.to_json(local_dpo_mapped_path)\n",
                "            \n",
                "    except Exception as e:\n",
                "        print(f\"Failed to load dataset from Hugging Face: {e}\")\n",
                "\n",
                "print(f\"SFT Samples: {len(sft_dataset) if sft_dataset else 0}\")\n",
                "print(f\"DPO Samples: {len(dpo_dataset) if dpo_dataset else 0}\")"
            ]
            print("  Updated dataset loading/mapping/caching block.")
            break

    # 4. Add average_tokens_across_devices=False to TrainingArguments (SFT) and DPOConfig (DPO) to fix AttributeError: 'int' object has no attribute 'mean'
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and 'sft_training_args = TrainingArguments(' in ''.join(cell['source']):
            new_source = []
            for line in cell['source']:
                if 'report_to="none"' in line:
                    line = line.replace('report_to="none"', 'report_to="none",\n    average_tokens_across_devices=False')
                new_source.append(line)
            cell['source'] = new_source
            print("  Added average_tokens_across_devices=False to SFT TrainingArguments.")
            
        if cell['cell_type'] == 'code' and 'dpo_config = DPOConfig(' in ''.join(cell['source']):
            new_source = []
            for line in cell['source']:
                if 'report_to="none"' in line:
                    line = line.replace('report_to="none"', 'report_to="none",\n    average_tokens_across_devices=False')
                new_source.append(line)
            cell['source'] = new_source
            print("  Added average_tokens_across_devices=False to DPO DPOConfig.")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("DPO notebook update completed.")

def update_baseline_notebook(filepath):
    print(f"Updating {filepath}...")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # 1. Update git clone command to BTC repo
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and any('!git clone' in line for line in cell['source']):
            new_source = []
            for line in cell['source']:
                if '!git clone' in line:
                    line = line.replace("https://github.com/VinAI-Research/car-bench-ijcai-vsf.git", "https://github.com/Logm12/car-bench-ijcai-vsf")
                    line = line.replace("car-bench-ijcai-vsf.git", "car-bench-ijcai-vsf")
                new_source.append(line)
            cell['source'] = new_source
            print("  Updated git clone command in baseline notebook.")
            break

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("Baseline notebook update completed.")

if __name__ == '__main__':
    update_orpo_notebook("notebooks/finetune_llm.ipynb")
    update_dpo_notebook("notebooks/finetune_llm_dpo.ipynb")
    update_baseline_notebook("notebooks/qwen_coder_baseline.ipynb")
