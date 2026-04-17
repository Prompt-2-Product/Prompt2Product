import json
import os

input_folder = "D:\FYP\Code spec Generator"   # change this
output_folder = "D:\FYP\Cleaned-Json2"    # change this

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if not filename.endswith(".txt"):
        continue

    filepath = os.path.join(input_folder, filename)
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract everything after "===== PRETTY JSON =====" 
    marker = "===== PRETTY JSON ====="
    if marker not in content:
        print(f"SKIPPED (no marker): {filename}")
        continue

    pretty_json_str = content.split(marker)[-1].strip()

    # Validate it parses correctly
    try:
        parsed = json.loads(pretty_json_str)
    except json.JSONDecodeError as e:
        print(f"INVALID JSON in {filename}: {e}")
        continue

    # Save as clean .json file with same base name
    out_name = filename.replace(".txt", ".json")
    out_path = os.path.join(output_folder, out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)

    print(f"OK: {filename} → {out_name}")

print("\nDone!")