import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

transcript_full_path = r"C:\Users\longm\.gemini\antigravity\brain\dcfedabd-d531-43f4-b108-d4aabd68f27f\.system_generated\logs\transcript_full.jsonl"

line_to_find = 344
with open(transcript_full_path, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        if line_num == line_to_find:
            data = json.loads(line)
            content = data.get("content", "")
            print("FOUND CONTENT:")
            print(content)
            break
