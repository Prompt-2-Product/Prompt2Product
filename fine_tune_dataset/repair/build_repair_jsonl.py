import json
from pathlib import Path

SYSTEM_PROMPT = (
    "You are a code repair assistant. "
    "Given a prompt, TaskSpec, error log, and broken files, "
    "return only valid JSON with a top-level key 'fixes'. "
    "Each item in 'fixes' must contain 'path' and corrected full file 'content'. "
    "Do not include markdown, explanations, or extra text."
)


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def read_json_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_user_content(prompt_text: str, taskspec: dict, error_text: str, broken_files: dict) -> str:
    parts = [
        "Prompt:",
        prompt_text,
        "",
        "TaskSpec:",
        json.dumps(taskspec, ensure_ascii=False, indent=2),
        "",
        "Error:",
        error_text,
        "",
        "Broken Files:",
        json.dumps(broken_files, ensure_ascii=False, indent=2),
    ]
    return "\n".join(parts)


def main():
    base_dir = Path(__file__).resolve().parent
    raw_cases_dir = base_dir / "raw_cases"
    output_file = base_dir / "repair_train.jsonl"

    if not raw_cases_dir.exists():
        raise FileNotFoundError(f"raw_cases folder not found: {raw_cases_dir}")

    case_dirs = sorted([p for p in raw_cases_dir.iterdir() if p.is_dir()])
    if not case_dirs:
        raise ValueError("No case folders found in raw_cases/")

    written_count = 0

    with output_file.open("w", encoding="utf-8") as fout:
        for case_dir in case_dirs:
            prompt_file = case_dir / "prompt.txt"
            taskspec_file = case_dir / "taskspec.json"
            error_file = case_dir / "error.txt"
            broken_files_file = case_dir / "broken_files.json"
            fixed_files_file = case_dir / "fixed_files.json"

            required_files = [
                prompt_file,
                taskspec_file,
                error_file,
                broken_files_file,
                fixed_files_file,
            ]

            missing = [str(f.name) for f in required_files if not f.exists()]
            if missing:
                print(f"Skipping {case_dir.name}: missing {', '.join(missing)}")
                continue

            try:
                prompt_text = read_text_file(prompt_file)
                taskspec = read_json_file(taskspec_file)
                error_text = read_text_file(error_file)
                broken_files = read_json_file(broken_files_file)
                fixed_files = read_json_file(fixed_files_file)
            except json.JSONDecodeError as e:
                print(f"Skipping {case_dir.name}: invalid JSON -> {e}")
                continue
            except Exception as e:
                print(f"Skipping {case_dir.name}: {e}")
                continue

            assistant_text = json.dumps(fixed_files, ensure_ascii=False)

            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_user_content(
                            prompt_text=prompt_text,
                            taskspec=taskspec,
                            error_text=error_text,
                            broken_files=broken_files,
                        ),
                    },
                    {"role": "assistant", "content": assistant_text},
                ]
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            written_count += 1

    print(f"Done. Wrote {written_count} repair samples to:")
    print(output_file)


if __name__ == "__main__":
    main()