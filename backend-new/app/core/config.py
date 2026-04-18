import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
FINETUNE_OUTPUTS_DIR = BASE_DIR.parent / "finetune" / "outputs"
DB_PATH = BASE_DIR / "app.db"

# Models Configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
ENHANCE_MODEL = "qwen2.5:7b-instruct"
TASKSPEC_MODEL_DIR = FINETUNE_OUTPUTS_DIR / "qwen_taskspec_only_lora_v3"
CODER_MODEL = "qwen-code-model"

MAX_LENGTH_TS = 1024

# Ports
PREVIEW_PORT_BASE = 8010 

os.makedirs(STORAGE_DIR, exist_ok=True)
