import re

def extract_json(text: str) -> str:
    """
    Robustly extract JSON object from LLM output.
    1. Removes Markdown code blocks.
    2. Finds the outer-most { ... }.
    """
    text = text.strip()
    
    # 1. Regex to find markdown blocks
    # Look for ```json ... ``` or just ``` ... ```
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        text = match.group(1)
        
    # 2. Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    
    if start != -1 and end != -1:
        text = text[start:end+1]
        
    return text
