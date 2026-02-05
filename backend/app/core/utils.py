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

def parse_traceback(error_text: str) -> list[tuple[str, int]]:
    """
    Parses a python traceback string to find (filename, linenum) tuples.
    Returns list of distinct files found in the trace.
    """
    # Regex for standard python trace: File "path/to/file.py", line 123, in func
    # Also handles some common variations
    matches = re.findall(r'File "(.*?)", line (\d+)', error_text)
    
    # Dedup and return
    seen = set()
    unique_matches = []
    for file, line in matches:
        if file not in seen:
            unique_matches.append((file, int(line)))
            seen.add(file)
            
    return unique_matches
