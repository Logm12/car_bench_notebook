from transformers import AutoTokenizer
import jinja2

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3.5-4B", trust_remote_code=True)
env = jinja2.Environment()
# Get compile source
source = env._parse(tokenizer.chat_template, None, None)
compiled_source = env.compile(tokenizer.chat_template, raw=True)
print("Compiled template python source code:")
print(compiled_source)
