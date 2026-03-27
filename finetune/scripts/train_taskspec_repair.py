import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig
from trl import SFTTrainer


# =========================
# Config
# =========================
BASE_MODEL = "Qwen/Qwen2.5-Coder-7B"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "fine_tune_dataset", "merged")

TRAIN_FILE = os.path.join(DATA_DIR, "train.jsonl")
VAL_FILE = os.path.join(DATA_DIR, "val.jsonl")

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_repair_lora")
LOGGING_DIR = os.path.join(PROJECT_ROOT, "finetune", "logs")

MAX_SEQ_LENGTH = 1024


def format_example(example):
    """
    Converts one chat-style JSONL record into a single text string
    for supervised fine-tuning.
    """
    messages = example["messages"]
    text_parts = []

    for msg in messages:
        role = msg["role"].strip().lower()
        content = msg["content"].strip()

        if role == "system":
            text_parts.append(f"<|system|>\n{content}")
        elif role == "user":
            text_parts.append(f"<|user|>\n{content}")
        elif role == "assistant":
            text_parts.append(f"<|assistant|>\n{content}")

    return {"text": "\n".join(text_parts)}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOGGING_DIR, exist_ok=True)

    print("Loading dataset...")
    dataset = load_dataset(
        "json",
        data_files={
            "train": TRAIN_FILE,
            "validation": VAL_FILE,
        },
    )

    dataset["train"] = dataset["train"].map(format_example)
    dataset["validation"] = dataset["validation"].map(format_example)

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading model in 4-bit...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    model.config.use_cache = False

    print("Setting LoRA config...")
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
        ],
    )

    print("Setting training arguments...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        overwrite_output_dir=True,
        num_train_epochs=2,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=4,
        eval_strategy="steps",
        eval_steps=20,
        save_strategy="steps",
        save_steps=20,
        logging_steps=5,
        learning_rate=2e-4,
        weight_decay=0.01,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        fp16=True,
        bf16=False,
        max_grad_norm=1.0,
        report_to="none",
        logging_dir=LOGGING_DIR,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )

    print("Creating trainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        args=training_args,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        packing=False,
    )

    print("Starting training...")
    trainer.train()

    print("Saving adapter and tokenizer...")
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("\nTraining complete.")
    print(f"Adapter saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()