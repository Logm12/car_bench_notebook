import json
import os

notebook_files = [
    "notebooks/qwen_coder_baseline.ipynb",
    "notebooks/finetune_llm.ipynb",
    "notebooks/finetune_llm_dpo.ipynb"
]

new_clone_source = [
    "# Check if running in Google Colab or Kaggle\n",
    "try:\n",
    "    import google.colab\n",
    "    IN_COLAB = True\n",
    "except ImportError:\n",
    "    IN_COLAB = False\n",
    "\n",
    "# Clone repository if running in a clean cloud VM\n",
    "import os\n",
    "if IN_COLAB or not os.path.exists(\"src\"):\n",
    "    print(\"Cloning repository to retrieve wiki.md policy and scripts...\")\n",
    "    !git clone --recursive https://github.com/CAR-bench/car-bench-ijcai.git\n",
    "    %cd car-bench-ijcai\n",
    "else:\n",
    "    print(\"Running in local workspace.\")\n",
    "\n",
    "# Robust check/fix for submodule/dependency content in third_party/car-bench\n",
    "if not os.path.exists(\"third_party/car-bench/pyproject.toml\"):\n",
    "    print(\"Submodule files missing in third_party/car-bench. Attempting to restore...\")\n",
    "    !git submodule update --init --recursive\n",
    "    if not os.path.exists(\"third_party/car-bench/pyproject.toml\"):\n",
    "        print(\"Directly cloning official car-bench dependency...\")\n",
    "        import shutil\n",
    "        if os.path.exists(\"third_party/car-bench\"):\n",
    "            try:\n",
    "                shutil.rmtree(\"third_party/car-bench\")\n",
    "            except Exception:\n",
    "                !rm -rf third_party/car-bench\n",
    "        !git clone --depth 1 https://github.com/CAR-bench/car-bench.git third_party/car-bench\n"
]

for nb_file in notebook_files:
    if not os.path.exists(nb_file):
        print(f"Skipping missing file: {nb_file}")
        continue
        
    print(f"Processing: {nb_file}")
    with open(nb_file, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
        
    updated = False
    
    # 1. Update the git clone / submodule setup cell
    for cell in nb_data["cells"]:
        if cell["cell_type"] == "code":
            source_str = "".join(cell["source"])
            if "git clone" in source_str and ("car-bench-ijcai-vsf" in source_str or "Logm12" in source_str):
                print(f"-> Updating clone cell in {nb_file}")
                cell["source"] = new_clone_source
                updated = True
                break
                
    # 2. Update the vLLM server parameters (mainly in qwen_coder_baseline.ipynb)
    if "qwen_coder_baseline" in nb_file:
        for cell in nb_data["cells"]:
            if cell["cell_type"] == "code":
                source_str = "".join(cell["source"])
                if "--disable-log-requests" in source_str:
                    print(f"-> Removing --disable-log-requests from vLLM cell in {nb_file}")
                    # Reconstruct source lines without --disable-log-requests line
                    new_lines = []
                    for line in cell["source"]:
                        if "--disable-log-requests" not in line:
                            new_lines.append(line)
                        else:
                            # Clean up trailing comma from previous line if necessary
                            if len(new_lines) > 0 and new_lines[-1].endswith(",\n"):
                                new_lines[-1] = new_lines[-1][:-2] + "\n"
                    cell["source"] = new_lines
                    updated = True
                    
    if updated:
        with open(nb_file, "w", encoding="utf-8") as f:
            json.dump(nb_data, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"Successfully updated: {nb_file}")
    else:
        print(f"No changes needed for: {nb_file}")
