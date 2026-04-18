import torch
import json
from unsloth import FastLanguageModel
from app.core.config import TASKSPEC_MODEL_DIR, MAX_LENGTH_TS

def generate_taskspec(prompt: str):
    """
    Loads model from path, generates TaskSpec JSON, unloads model from VRAM.
    """
    ts_model, ts_tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(TASKSPEC_MODEL_DIR), 
        load_in_4bit=True, 
        max_seq_length=MAX_LENGTH_TS,
    )
    FastLanguageModel.for_inference(ts_model)

    input_text = (
        f"<|system|>\n"
        f"Generate valid TaskSpec JSON only. Do not output markdown, comments, or explanation.\n"
        f"<|user|>\n{prompt}\n"
        f"<|assistant|>\n"
    )
    
    inputs = ts_tokenizer(input_text, return_tensors="pt").to("cuda")
    input_len = inputs["input_ids"].shape[1]
    max_new = max(50, MAX_LENGTH_TS - input_len - 10)

    try:
        with torch.no_grad():
            outputs = ts_model.generate(
                **inputs, 
                max_new_tokens=max_new, 
                temperature=0.3,
                top_p=0.9, 
                repetition_penalty=1.05, 
                do_sample=True,
            )
        full = ts_tokenizer.decode(outputs[0], skip_special_tokens=True)
        raw = full.split("<|assistant|>")[-1].strip()
        parsed = json.loads(raw)
        return raw, parsed
    finally:
        del ts_model
        del ts_tokenizer
        torch.cuda.empty_cache()
