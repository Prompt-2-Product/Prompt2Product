import os

# Append modifier.py
with open(r"d:\FYP\backend\app\services\modifier.py", "a", encoding="utf-8") as f_out:
    with open(r"d:\FYP\modifier.py", "r", encoding="utf-8") as f_in:
        f_out.write("\n\n# --- Appended from Claude's modifier.py --- \n\n")
        f_out.write(f_in.read())

# Append patcher.py
with open(r"d:\FYP\backend\app\services\patcher.py", "a", encoding="utf-8") as f_out:
    with open(r"d:\FYP\patcher.py", "r", encoding="utf-8") as f_in:
        f_out.write("\n\n# --- Appended from Claude's patcher.py --- \n\n")
        f_out.write(f_in.read())

print("Files merged successfully.")
