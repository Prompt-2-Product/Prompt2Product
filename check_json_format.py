import json
import sys

def check_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = f.read()
        
        # Try direct load
        try:
            json.loads(data)
            print("OK: Standard JSON")
            return
        except json.JSONDecodeError as e:
            print(f"Standard JSON error: {e}")

        # Try wrapping in array
        try:
            json.loads("[" + data + "]")
            print("OK: JSON fragments (objects separated by commas?)")
            return
        except json.JSONDecodeError as e:
            print(f"Array wrap error: {e}")

        # Try JSONL (assuming each object is on one line? No, they are multiline)
        # We might need a proper parser for multiple objects.
        
    except Exception as e:
        print(f"File error: {e}")

if __name__ == "__main__":
    check_json(sys.argv[1])
