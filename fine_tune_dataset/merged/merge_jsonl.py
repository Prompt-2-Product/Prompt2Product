from pathlib import Path


def main():
    base_dir = Path(__file__).resolve().parent
    root_dir = base_dir.parent

    taskspec_file = root_dir / "taskspec" / "taskspec_train.jsonl"
    repair_file = root_dir / "repair" / "repair_train.jsonl"
    output_file = base_dir / "merged_raw.jsonl"

    for file_path in [taskspec_file, repair_file]:
        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")

    merged_lines = []

    for file_path in [taskspec_file, repair_file]:
        with file_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            merged_lines.extend(lines)

    with output_file.open("w", encoding="utf-8") as f:
        for line in merged_lines:
            f.write(line + "\n")

    print(f"Merged {len(merged_lines)} samples into:")
    print(output_file)


if __name__ == "__main__":
    main()