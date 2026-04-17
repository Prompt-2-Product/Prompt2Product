import json
import os

def merge_giki_datasets():
    # 1. Define your file paths
    fixed_code_gen = "code-gen-data-FIXED.json"
    previous_batches = [
        "finetune_dataset_v3_1.json",
        "finetune_dataset_v3_batch2.json",
        "finetune_dataset_v3_batch3.json",
        "finetune_dataset_v3_batch4.json"
    ]
    
    master_list = []

    # 2. Load the newly repaired 25 samples
    if os.path.exists(fixed_code_gen):
        with open(fixed_code_gen, 'r', encoding='utf-8') as f:
            data = json.load(f)
            master_list.extend(data)
            print(f"Added {len(data)} samples from {fixed_code_gen}")
    else:
        print(f"Error: {fixed_code_gen} not found.")

    # 3. Load the previous 21 samples
    for file in previous_batches:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure we handle both lists and single objects
                if isinstance(data, list):
                    master_list.extend(data)
                else:
                    master_list.append(data)
                print(f"Added samples from {file}")
        else:
            print(f"Warning: {file} not found. Skipping...")

    # 4. Final Validation & Output
    # ensure_ascii=False keeps your weather symbols (like °C) intact
    with open("MASTER_TRAINING_DATA.json", "w", encoding="utf-8") as f:
        json.dump(master_list, f, indent=2, ensure_ascii=False)
    
    print("-" * 30)
    print(f"SUCCESS: Total of {len(master_list)} samples merged.")
    print("File saved as: MASTER_TRAINING_DATA.json")

if __name__ == "__main__":
    merge_giki_datasets()