import json
import re

def fix_content_quotes(raw_text):
    # Find all content fields
    pattern = r'"content":\s*"(.*?)"', re.DOTALL

    def escape_inner_quotes(match):
        content = match.group(1)

        # Escape quotes that are NOT already escaped
        content = re.sub(r'(?<!\\)"', r'\\"', content)

        return f'"content": "{content}"'

    fixed = re.sub(pattern, escape_inner_quotes, raw_text)

    return fixed


def main():
    with open("input.txt", "r", encoding="utf-8") as f:
        raw = f.read()

    fixed = fix_content_quotes(raw)

    # Wrap into list if needed
    if not fixed.strip().startswith("["):
        fixed = "[\n" + fixed.strip().rstrip(",") + "\n]"

    with open("fixed.json", "w", encoding="utf-8") as f:
        f.write(fixed)

    print("✅ JSON FIXED and saved as fixed.json")


if __name__ == "__main__":
    main()