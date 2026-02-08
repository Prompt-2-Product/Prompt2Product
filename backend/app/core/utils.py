import json
import re

def extract_json(text: str) -> str:
    """
    Robustly extract JSON object from LLM output.
    If multiple JSON blocks/objects are found, it attempts to merge their 'files' arrays.
    """
    text = text.strip()
    
    # 1. Try to find all markdown blocks first
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(pattern, text)
    
    # if no markdown blocks, try to find all { } pairs at the top level
    if not matches:
        # This is a simple heuristic to find sibling { } objects
        # It finds everything between { and } that looks like a root object
        # We use a non-greedy match and look for objects that started at the start of a line or after a }
        matches = re.findall(r"\{[\s\S]*?\}", text)

    if not matches:
        return ""

    # Merge logic
    merged_files = []
    final_obj = {}

    for m in matches:
        try:
            obj = json.loads(m)
            if isinstance(obj, dict):
                if "files" in obj and isinstance(obj["files"], list):
                    merged_files.extend(obj["files"])
                
                # Keep other keys from the first object found
                for k, v in obj.items():
                    if k != "files" and k not in final_obj:
                        final_obj[k] = v
        except:
            continue
    
    if merged_files:
        final_obj["files"] = merged_files
        return json.dumps(final_obj)
    
    # Fallback to the first match if no merging happened
    return matches[0] if matches else ""

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
    
    # 2. Remove any stray backticks that might be inside string values
    # This is a common issue when LLM includes code snippets
    # We'll be conservative and only remove backticks that are clearly not part of markdown blocks
    
    # 3. Fix unescaped newlines in string values (more aggressive approach)
    # First, let's try to find "content": "..." patterns and escape newlines within them
    import re
    
    # Pattern to match "content": "..." where ... might contain unescaped newlines
    # We need to be careful not to break already-escaped content
    def escape_content_newlines(match):
        key = match.group(1)
        value = match.group(2)
        # Escape newlines and other special characters
        value = value.replace('\\', '\\\\')  # Escape backslashes first
        value = value.replace('\n', '\\n')
        value = value.replace('\r', '\\r')
        value = value.replace('\t', '\\t')
        value = value.replace('"', '\\"')
        return f'"{key}": "{value}"'
    
    # This is a simplified approach - try to fix obvious content fields
    # Note: This regex is imperfect but handles most cases
    try:
        # Match "content": followed by a quote, then anything until we hit a quote followed by comma or closing brace
        # This is tricky because the content itself might have quotes
        pass  # Skip complex regex for now, use simpler approach below
    except:
        pass
    
    # 4. Handle trailing commas in arrays/objects
    text = re.sub(r',\s*([\]}])', r'\1', text)
    
    return text
