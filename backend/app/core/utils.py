import re

def extract_json(text: str) -> str:
    """
    Robustly extract JSON object from LLM output.
    1. Removes Markdown code blocks.
    2. Finds the outer-most { ... }.
    3. Throws error if multiple { } blocks are detected at top level.
    """
    text = text.strip()
    
    # 1. Regex to find markdown blocks
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(pattern, text)
    if matches:
        if len(matches) > 1:
            raise ValueError("Multiple JSON blocks detected. Please merge into one.")
        text = matches[0]
        
    # 2. Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    
    if start == -1 or end == -1 or end <= start:
        return "" # No JSON found
    
    # Check for multiple { } pairs outside of the main one in the remaining text
    # if we strip the outer one and find another { we might have sibling objects
    # but that's complex to parse perfectly with regex. 
    # Let's count occurrences of "}{" or "}\n{" which often indicate sibling blocks.
    siblings = re.findall(r"\}\s*\{", text)
    if siblings:
         raise ValueError("Multiple sibling JSON objects detected. Please merge into one 'files' list.")
        
    return text[start:end+1]

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
def clean_requirements_text(content: str) -> str:
    """
    Strips all version numbers, constraints, and extras from requirements.txt content.
    Returns only valid package names.
    """
    lines = content.splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Extract only valid package name characters from the start
        match = re.match(r"^([a-zA-Z0-9\-_.]+)", line)
        if match:
            cleaned_lines.append(match.group(1))
    
    result = "\n".join(cleaned_lines)
    if result:
        result += "\n"
    return result

def repair_json(text: str) -> str:
    """
    Experimental 'dirty' JSON fixer for common LLM mistakes.
    """
    # 1. Fix 'code_files' -> 'files' alias
    text = text.replace('"code_files":', '"files":')
    
    # 2. Fix unescaped newlines in string values
    # Matches any "key": "value" where value contains newlines
    def fix_newlines(match):
        prefix = match.group(1)
        content = match.group(2)
        # Escape internal newlines but preserve the quotes
        content = content.replace('\n', '\\n').replace('\r', '')
        return f'{prefix}"{content}"'
    
    # This regex is safer: it finds key-value pairs where the value starts with " and ends with "
    # but might have newlines in between.
    text = re.sub(r'(".*?"\s*:\s*)"([\s\S]*?)"(?=\s*[,}\]])', fix_newlines, text)
    
    # 3. Handle trailing commas in arrays/objects
    text = re.sub(r',\s*([\]}])', r'\1', text)
    
    return text
