import json
import random
from pathlib import Path

SYSTEM_PROMPT = "Generate valid TaskSpec JSON only. Do not output markdown, comments, or explanation."

def main():
    base_dir = Path(__file__).resolve().parent
    prompts_dir = base_dir / "prompts"
    samples_dir = base_dir / "samples"
    target_dir = base_dir.parent / "taskspec_only"
    
    prompt_files = sorted(prompts_dir.glob("prompt_*.txt"))
    all_records = []
    for pf in prompt_files:
        num = pf.stem.split("_")[-1]
        sf = samples_dir / f"sample_{num}.json"
        if not sf.exists(): continue
        
        prompt = pf.read_text(encoding="utf-8").strip()
        sample = json.loads(sf.read_text(encoding="utf-8"))
        ans = json.dumps(sample, ensure_ascii=False)
        
        all_records.append({"messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": ans}
        ]})

    random.seed(42)
    random.shuffle(all_records)
    train, val = all_records[:-10], all_records[-10:]

    with (target_dir / "train.jsonl").open("w", encoding="utf-8") as f:
        for r in train: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (target_dir / "val.jsonl").open("w", encoding="utf-8") as f:
        for r in val: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(train)} train, {len(val)} val.")

if __name__ == "__main__": main()
