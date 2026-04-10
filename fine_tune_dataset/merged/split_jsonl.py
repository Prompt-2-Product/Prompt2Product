import random
from pathlib import Path


def main():
    random.seed(42)

    base_dir = Path(__file__).resolve().parent
    input_file = base_dir / "merged_raw.jsonl"
    train_file = base_dir / "train.jsonl"
    val_file = base_dir / "val.jsonl"

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with input_file.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        raise ValueError("Not enough samples to split.")

    random.shuffle(lines)

    split_idx = int(len(lines) * 0.9)  # 90% train, 10% validation
    train_lines = lines[:split_idx]
    val_lines = lines[split_idx:]

    with train_file.open("w", encoding="utf-8") as f:
        for line in train_lines:
            f.write(line + "\n")

    with val_file.open("w", encoding="utf-8") as f:
        for line in val_lines:
            f.write(line + "\n")

    print(f"Total samples: {len(lines)}")
    print(f"Train samples: {len(train_lines)}")
    print(f"Validation samples: {len(val_lines)}")
    print(f"\nSaved train file to:\n{train_file}")
    print(f"\nSaved validation file to:\n{val_file}")


if __name__ == "__main__":
    main()