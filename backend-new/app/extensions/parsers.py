import re
import json

def safe_parse(text: str):
    start = text.find("{")
    if start == -1:
        return None
    text = text[start:].strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()

    # Fix JS template literals ${...} → {...}
    text = re.sub(r'\$\{([^}]*)\}', r'{\1}', text)

    # Fix missing newline between import statements
    text = re.sub(r'(import\s+\w+)\s+(from\s+)', r'\1\\n\2', text)

    # Pass 1: strip // comments outside strings
    cleaned_comments = []
    in_string = escape = False
    i = 0
    while i < len(text):
        ch = text[i]
        if escape:
            cleaned_comments.append(ch); escape = False; i += 1; continue
        if ch == "\\" and in_string:
            escape = True; cleaned_comments.append(ch); i += 1; continue
        if ch == '"':
            in_string = not in_string; cleaned_comments.append(ch); i += 1; continue
        if not in_string and ch == "/" and i + 1 < len(text) and text[i+1] == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        cleaned_comments.append(ch)
        i += 1
    text = "".join(cleaned_comments)

    # Pass 2: escape unescaped control chars + fix invalid escape sequences
    result = []
    in_string = escape = False
    for ch in text:
        if escape:
            if ch in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'):
                result.append('\\')
                result.append(ch)
            else:
                result.append(ch)   # drop bad backslash
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string; result.append(ch); continue
        if in_string:
            if ch == "\n": result.append("\\n")
            elif ch == "\r": pass
            elif ch == "\t": result.append("\\t")
            else: result.append(ch)
        else:
            result.append(ch)

    cleaned = "".join(result)

    try:
        return json.loads(cleaned)
    except:
        pass

    # Bracket repair
    stack = []
    in_str = escape = False
    for ch in cleaned:
        if escape: escape = False; continue
        if ch == "\\" and in_str: escape = True; continue
        if ch == '"': in_str = not in_str; continue
        if in_str: continue
        if ch in "{[": stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack: stack.pop()
    try:
        return json.loads(cleaned + "".join(reversed(stack)))
    except:
        return None

def normalize_result(data: dict) -> dict:
    if not isinstance(data, dict):
        return data

    manifest = data.get("manifest", [])
    if isinstance(manifest, dict):
        data["manifest"] = manifest.get("files", list(manifest.keys()))
    elif not isinstance(manifest, list):
        data["manifest"] = []

    files = data.get("files", [])
    normalized = []

    if isinstance(files, dict):
        for path, value in files.items():
            if isinstance(value, str):
                if value.strip():
                    normalized.append({"path": path, "content": value})
            elif isinstance(value, dict):
                content = value.get("content", "")
                if content.strip():
                    normalized.append({"path": path, "content": content})
            elif value is not None:
                try:
                    normalized.append({"path": path, "content": str(value)})
                except:
                    pass

    elif isinstance(files, list):
        for f in files:
            if isinstance(f, dict):
                path = f.get("path", f.get("name", "")).strip()
                content = f.get("content", "")
                if isinstance(content, dict):
                    content = content.get("code", content.get("content", str(content)))
                if not path:
                    continue
                if content.strip():
                    normalized.append({"path": path, "content": content})

    data["files"] = normalized
    return data
