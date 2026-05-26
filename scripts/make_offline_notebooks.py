import json
import os
import copy

def transform_to_offline(input_path, output_path, is_dpo=False):
    if not os.path.exists(input_path):
        print(f"Input notebook {input_path} not found.")
        return
        
    print(f"Reading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    offline_nb = copy.deepcopy(nb)
    
    # 1. Modify Header Title in cell 0
    if len(offline_nb["cells"]) > 0 and offline_nb["cells"][0]["cell_type"] == "markdown":
        lines = offline_nb["cells"][0]["source"]
        for idx, line in enumerate(lines):
            if line.startswith("# CAR-bench Agent Alignment:"):
                lines[idx] = line.replace("Pipeline", "Pipeline (Local Offline Workstation)")
                
    # 2. Iterate through cells and apply modifications
    new_cells = []
    for cell in offline_nb["cells"]:
        if cell["cell_type"] == "code":
            source_code = "".join(cell["source"])
            
            # Case A: Colab check and Git clone
            if "google.colab" in source_code and "!git clone" in source_code:
                cell["source"] = [
                    "# Running in local offline workstation environment\n",
                    "IN_COLAB = False\n",
                    "print(\"Running on local workstation. Repositories and paths are assumed local.\")"
                ]
            
            # Case B: Pip packages installation
            elif "!pip install" in source_code:
                cell["source"] = [
                    "# Ensure you have installed these packages in your local environment:\n",
                    "# pip install transformers peft trl datasets accelerate bitsandbytes huggingface_hub protobuf matplotlib seaborn\n",
                    "# pip install \"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git\"\n",
                    "print(\"Please verify packages are pre-installed in your virtual environment.\")"
                ]
                
            # Case C: Google Drive Mount and Kaggle outputs config
            elif "google.colab import drive" in source_code:
                cell["source"] = [
                    "# Local output directory configured for local PC\n",
                    "PERSISTENT_DIR = \"./outputs\"\n",
                    "os.makedirs(PERSISTENT_DIR, exist_ok=True)\n",
                    "print(f\"Target checkpoints directory configured locally: {PERSISTENT_DIR}\")"
                ]
                
            # Case D: Colab interactive file uploads
            elif "from google.colab import files" in source_code and "files.upload()" in source_code:
                # Keep log parsing, remove files.upload() block
                cell_source = []
                for line in cell["source"]:
                    if "from google.colab import files" in line or "uploaded = files.upload()" in line or "uploaded.keys()" in line or "files.upload()" in line:
                        continue
                    if "Interactive upload not available" in line:
                        cell_source.append("        print(\"Interactive upload is disabled on local offline PC. Falling back to log parsing.\")\n")
                        continue
                    cell_source.append(line)
                cell["source"] = cell_source
                
            # Case E: download calls in GGUF export or download section
            elif "files.download(" in source_code:
                # Remove Colab download block from GGUF export cell or zip download helper
                cell_source = []
                in_colab_block = False
                for line in cell["source"]:
                    if "if IN_COLAB:" in line:
                        in_colab_block = True
                        continue
                    if in_colab_block:
                        # Skip indented lines inside the colab block
                        if line.startswith(" ") or line.startswith("\t") or line == "\n" or line.strip() == "":
                            continue
                        else:
                            in_colab_block = False
                    cell_source.append(line)
                cell["source"] = cell_source
                
        new_cells.append(cell)
        
    offline_nb["cells"] = new_cells
    
    print(f"Writing offline notebook to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(offline_nb, f, indent=1)

if __name__ == "__main__":
    os.makedirs("notebooks", exist_ok=True)
    transform_to_offline("notebooks/finetune_llm.ipynb", "notebooks/offline_finetune_llm_local_pc.ipynb", is_dpo=False)
    transform_to_offline("notebooks/finetune_llm_dpo.ipynb", "notebooks/offline_finetune_llm_dpo_local_pc.ipynb", is_dpo=True)
    print("Done generating offline notebooks.")
