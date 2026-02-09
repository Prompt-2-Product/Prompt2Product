import re

# Read the new function
with open('post_process_fix.py', 'r', encoding='utf-8') as f:
    new_function = f.read()

# Read the original file
with open('app/services/code_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the old function
pattern = r'def post_process_output\(output: GenOutput\) -> GenOutput:.*?(?=\nasync def llm_spec_to_code)'
replacement = new_function.strip() + '\n'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('app/services/code_generator.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully replaced post_process_output function!")
