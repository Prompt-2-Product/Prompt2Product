import json
from pathlib import Path


SYSTEM_PROMPT = (
    "Generate valid TaskSpec JSON only. "
    "Do not output markdown, comments, or explanation."
)


def main():
    base_dir = Path(__file__).resolve().parent
    prompts_dir = base_dir / "prompts"
    samples_dir = base_dir / "samples"
    output_file = base_dir / "taskspec_train.jsonl"

    if not prompts_dir.exists():
        raise FileNotFoundError(f"Prompts folder not found: {prompts_dir}")

    if not samples_dir.exists():
        raise FileNotFoundError(f"Samples folder not found: {samples_dir}")

    prompt_files = sorted(prompts_dir.glob("prompt_*.txt"))
    if not prompt_files:
        raise ValueError("No prompt files found in prompts/ folder.")

    written_count = 0

    with output_file.open("w", encoding="utf-8") as fout:
        for prompt_file in prompt_files:
            number = prompt_file.stem.split("_")[-1]
            sample_file = samples_dir / f"sample_{number}.json"

            if not sample_file.exists():
                print(f"Skipping prompt_{number}: missing {sample_file.name}")
                continue

            prompt_text = prompt_file.read_text(encoding="utf-8").strip()

            try:
                sample_data = json.loads(sample_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"Skipping sample_{number}: invalid JSON -> {e}")
                continue

            assistant_text = json.dumps(sample_data, ensure_ascii=False)

            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_text},
                    {"role": "assistant", "content": assistant_text},
                ]
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            written_count += 1

    print(f"Done. Wrote {written_count} samples to:")
    print(output_file)


if __name__ == "__main__":
    main()