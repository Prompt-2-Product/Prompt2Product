---
noteId: "f2c0abd039d011f1b7676b5e5c1b1314"
tags: []

---

# Prompt2Product — Project Documentation
## Methodology, Workflow, Architecture & Solution

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Proposed Solution](#3-proposed-solution)
4. [System Architecture](#4-system-architecture)
5. [Technology Stack](#5-technology-stack)
6. [AI/ML Methodology](#6-aiml-methodology)
7. [Core Pipeline Workflow](#7-core-pipeline-workflow)
8. [Module-Level Design](#8-module-level-design)
9. [Database Design](#9-database-design)
10. [Fine-Tuning Methodology](#10-fine-tuning-methodology)
11. [Sandbox & Isolation Strategy](#11-sandbox--isolation-strategy)
12. [Frontend Architecture](#12-frontend-architecture)
13. [Modification & Feedback Loop](#13-modification--feedback-loop)
14. [Deployment & Infrastructure](#14-deployment--infrastructure)
15. [Data Flow Diagrams](#15-data-flow-diagrams)
16. [Evaluation & Quality Gates](#16-evaluation--quality-gates)
17. [Limitations & Future Work](#17-limitations--future-work)

---

## 1. Project Overview

**Prompt2Product** is an autonomous, end-to-end AI-powered web application generator. Given a single natural language prompt (e.g., *"Build a recipe sharing platform"*), the system produces a fully functional web application with a FastAPI backend and an HTML/CSS/JavaScript frontend, runs it inside an isolated virtual environment, and presents a live preview — all without any human intervention beyond the initial prompt.

The system is built as a **Final Year Project (FYP)** and demonstrates a chained, multi-stage Large Language Model (LLM) pipeline combined with fine-tuned domain-specific models and automated error repair.

---

## 2. Problem Statement

Building a functional web application from scratch requires expertise across multiple domains: UI/UX design, frontend development, backend API design, database modelling, and DevOps. Even experienced developers spend significant time on boilerplate, wiring, and iteration.

Existing AI coding assistants (GitHub Copilot, ChatGPT, etc.) operate as *co-pilots* — they respond to individual prompts but do not:

- Autonomously architect and generate a complete, multi-file project.
- Execute the generated code and verify it actually runs.
- Repair runtime errors without human intervention.
- Allow the user to request changes in plain English post-generation.

**Prompt2Product fills this gap** by acting as a fully autonomous software engineer that takes a prompt, plans the architecture, writes the code, runs it, fixes errors, and allows iterative refinement — all through natural language.

---

## 3. Proposed Solution

The solution is a **multi-stage LLM orchestration pipeline** structured as follows:

```
User Prompt
    │
    ▼
[Stage 0] Prompt Enhancement       ← General-purpose LLM
    │
    ▼
[Stage 1] Specification Generation ← Fine-tuned TaskSpec Model
    │
    ▼
[Stage 2] Code Generation          ← Fine-tuned Coder Model
    │
    ▼
[Stage 3] File Validation          ← Rule-based quality checks
    │
    ▼
[Stage 4] Venv Sandbox Setup       ← Isolated Python environment
    │
    ▼
[Stage 5] Dependency Installation  ← pip install
    │
    ▼
[Stage 6] Run + Auto-Repair Loop   ← Fine-tuned Repair Model (up to 2 attempts)
    │
    ▼
Live Preview (iframe embed)
    │
    ▼
[Optional] User Modification Loop  ← Fine-tuned Coder Model
```

Each stage is handled by a dedicated module, allowing independent testing, fine-tuning, and replacement of individual components without affecting the whole pipeline.

---

## 4. System Architecture

### 4.1 High-Level Architecture

The system is composed of three top-level layers:

| Layer | Technology | Role |
|-------|-----------|------|
| **Frontend** | Next.js (React 18, TypeScript) | User interface, prompt input, live preview, log streaming |
| **Backend** | FastAPI (Python 3.9+) | Orchestration API, pipeline execution, workspace management |
| **AI Layer** | Ollama / OpenAI-compatible LLMs | LLM inference for all generation and repair tasks |

These three layers communicate over HTTP and are containerised with Docker Compose for reproducible deployment.

### 4.2 Backend Internal Architecture

The backend is organised into the following sub-systems:

```
backend/app/
├── api/                  ← FastAPI route handlers (HTTP layer)
├── core/
│   ├── config.py         ← Environment-based configuration
│   ├── models.py         ← SQLModel database models
│   └── utils.py          ← JSON repair, traceback parsing, helpers
├── llm/
│   ├── providers/
│   │   ├── ollama_client.py       ← Ollama (local) LLM client
│   │   └── openai_compat_client.py ← OpenAI-compatible LLM client
│   └── router.py         ← Model routing (spec/code/repair/enhance)
├── services/
│   ├── orchestrator.py   ← Master pipeline controller
│   ├── prompt_enhancer.py ← Stage 0: Prompt enrichment
│   ├── spec_generator.py  ← Stage 1: TaskSpec JSON generation
│   ├── code_generator.py  ← Stage 2: Full-stack code generation
│   ├── modifier.py        ← Modification pipeline
│   └── repair.py          ← Runtime error repair
├── sandbox/
│   └── venv_runner.py    ← Isolated venv execution
├── patcher.py            ← Patch parsing and application
└── workspace.py          ← File I/O and workspace management
```

---

## 5. Technology Stack

### 5.1 Backend

| Component | Technology | Version/Notes |
|-----------|-----------|---------------|
| Web Framework | FastAPI | Python 3.9+ |
| ORM | SQLModel | Built on SQLAlchemy + Pydantic |
| Database | SQLite | File-based, no external DB server needed |
| HTTP Server | Uvicorn | ASGI, used both for the main API and generated apps |
| HTTP Client | httpx | Async HTTP calls to LLM providers |
| Runtime Isolation | Python venv | One per generated application run |

### 5.2 Frontend

| Component | Technology |
|-----------|-----------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| UI Styling | Bootstrap + custom CSS |
| State Management | React hooks (useState, useEffect) |
| API Communication | Native Fetch API |

### 5.3 AI / LLM

| Component | Technology |
|-----------|-----------|
| Local LLM Runtime | Ollama |
| Base Models | Qwen2.5-Coder-3B-Instruct (fine-tuned), Qwen2.5:7B-Instruct (general) |
| Fine-Tuning Framework | Hugging Face TRL + PEFT (LoRA) |
| Quantization | BitsAndBytes (4-bit NF4) |
| Alternative Provider | OpenAI-compatible API (works with Claude, GPT-4, etc.) |

### 5.4 Infrastructure

| Component | Technology |
|-----------|-----------|
| Containerisation | Docker + Docker Compose |
| Port Management | Dynamic allocation (base port 8010 + run_id) |
| Storage | SQLite DB + local filesystem workspace directories |

---

## 6. AI/ML Methodology

### 6.1 Philosophy: Specialised Small Models over One Large Model

A core design decision is to use **multiple fine-tuned small models** (Qwen2.5-Coder-3B) instead of a single large general-purpose model. This choice is motivated by:

- **Cost & Latency:** 3B parameter models run on consumer-grade hardware (8–16 GB VRAM) with Ollama, making the system self-hosted and free to run.
- **Task Specialisation:** Each stage requires a different "style" of output (JSON spec, multi-file code, unified diff patch). Fine-tuning a dedicated model per task produces significantly more reliable outputs than prompting a general model.
- **Independent Upgradeability:** Each model can be retrained independently as more data is collected.

### 6.2 Model Roles

| Model | Task | Input | Output |
|-------|------|-------|--------|
| `enhance_model` | Prompt enrichment | Vague user prompt | Rich architectural description |
| `spec_model` | Architecture planning | Enriched prompt | TaskSpec JSON object |
| `code_model` | Full-stack code generation | TaskSpec JSON | GenOutput (files list) |
| `repair_model` | Runtime error repair | Error traceback + file context | Unified diff patch |

### 6.3 LLM Abstraction Layer

A factory pattern (`llm/router.py`) decouples the pipeline from the LLM provider. The `ModelRouter` class exposes four methods: `spec_model()`, `code_model()`, `repair_model()`, `enhance_model()`. Each returns a configured `LLMClient` instance pointing to either Ollama or an OpenAI-compatible endpoint, determined by the `LLM_MODE` environment variable.

This means the entire system can switch from locally-hosted Qwen models to Claude or GPT-4 with a single configuration change — no code changes required.

---

## 7. Core Pipeline Workflow

### Stage 0 — Prompt Enhancement (`prompt_enhancer.py`)

**Purpose:** Convert a vague, short user prompt into a rich, actionable architectural description.

**Input:** `"e-commerce platform"`

**Process:** The enhancement LLM (general-purpose Qwen 7B) is instructed to expand the input into a 1–2 sentence description that names the application type, key features, and implied constraints.

**Output:** `"Build a modern e-commerce platform with product listings, user authentication, shopping cart, order management, and an admin dashboard. The system should support real-time inventory updates and payment gateway integration."`

**Why this stage exists:** Feeding vague prompts directly into the spec generator produces shallow, generic architectures. Enrichment primes the downstream models with enough context to generate meaningful pages, routes, and data models.

---

### Stage 1 — Specification Generation (`spec_generator.py`)

**Purpose:** Transform the enriched prompt into a structured, machine-readable architectural blueprint (`TaskSpec`).

**Input:** Enhanced prompt string.

**Output:** A `TaskSpec` JSON object with the following schema:

```json
{
  "app_name": "ShopEase",
  "pages": [
    {
      "name": "Home",
      "sections": ["Hero banner", "Featured products grid", "Newsletter signup"]
    },
    ...
  ],
  "api": [
    { "method": "GET",  "path": "/products",         "desc": "List all products" },
    { "method": "POST", "path": "/cart/add",          "desc": "Add item to cart"  },
    ...
  ],
  "data_models": [
    {
      "name": "Product",
      "fields": { "id": "int", "name": "str", "price": "float", "stock": "int" }
    },
    ...
  ],
  "styling": {
    "theme": "light",
    "primary_color": "#2563EB"
  },
  "constraints": {
    "frontend": "HTML/CSS/JS",
    "backend": "FastAPI"
  }
}
```

**JSON Repair:** LLMs occasionally produce malformed JSON (smart quotes, trailing commas, mismatched braces). The `core/utils.py` module implements a multi-strategy JSON repair pipeline:
1. Direct `json.loads()` attempt.
2. Smart-quote normalisation and re-parse.
3. Balanced-brace extraction (tracks depth, ignores content inside strings).
4. Regex-based extraction of the outermost `{...}` block.

---

### Stage 2 — Code Generation (`code_generator.py`)

**Purpose:** Generate all source files for the application from the TaskSpec.

**Input:** `TaskSpec` object.

**Output:** `GenOutput` — a structured object containing:
- `files`: List of `GenFile(path, content)` objects (HTML pages, CSS, JS, Python backend, requirements.txt).
- `plan`: Narrative description of the generation strategy.
- `manifest`: List of key components created.
- `entrypoint`: Path to the backend entry point (typically `backend/main.py`).

**Post-Processing:**
The raw LLM output undergoes several normalisation steps before being written to disk:

1. **Escaped newline repair:** LLMs sometimes output literal `\n` instead of real newlines. These are replaced.
2. **Route injection:** The backend `main.py` is scanned for `@app.get()` decorators. Any HTML page in the `frontend/` directory that lacks a corresponding route gets one injected automatically.
3. **StaticFiles check:** Ensures `app.mount("/static", StaticFiles(...))` is present so the frontend can serve CSS/JS.
4. **FileResponse import check:** Confirms `from fastapi.responses import FileResponse` is present.

---

### Stage 3 — File Validation (`orchestrator.py`)

**Purpose:** Non-blocking quality gate that warns about likely generation failures before attempting to run.

**Checks performed:**

| Check | Criteria |
|-------|----------|
| Lorem ipsum detection | HTML files must not contain `Lorem ipsum` placeholder text |
| Generic placeholder detection | HTML must not contain patterns like `Feature 1`, `Feature 2`, `Service N` |
| CSS minimum length | CSS files must be ≥ 50 lines |
| JS minimum length | JS files must be ≥ 30 lines |
| Backend route presence | `main.py` must contain at least one `@app.get()` decorator |
| FileResponse import | `main.py` must import `FileResponse` |

Failures at this stage are logged as warnings but do not stop the pipeline. The rationale is that the repair loop in Stage 6 may still recover from minor issues.

---

### Stage 4 — Venv Sandbox Setup (`sandbox/venv_runner.py`)

**Purpose:** Create a fully isolated Python virtual environment for the generated application so it cannot interfere with the host system or other generated apps.

**Process:**
1. `python -m venv .venv_sandbox` — Creates the virtual environment inside the run's workspace directory.
2. Pre-installs core dependencies: `fastapi`, `uvicorn`, `aiofiles`.
3. Workspace path is structured as: `storage/workspaces/project_{id}/run_{id}/`.

---

### Stage 5 — Dependency Installation (`sandbox/venv_runner.py`)

**Purpose:** Install the application's specific Python dependencies from its `requirements.txt`.

**Process:**
1. Read `generated_app/backend/requirements.txt`.
2. Clean package names (strip version pins that may cause resolution conflicts).
3. Run `pip install` inside the venv with a 120-second timeout.
4. Failures are captured and trigger the repair loop.

---

### Stage 6 — Run & Auto-Repair Loop (`orchestrator.py` + `repair.py`)

**Purpose:** Start the generated application and automatically fix any runtime errors.

**Loop (maximum `MAX_REPAIR_ATTEMPTS = 2` iterations):**

```
1. Syntax Check
   └─ python -m py_compile on all .py files
   └─ If syntax error: extract error, go to Repair

2. Start Uvicorn
   └─ Spawn subprocess on port (8010 + run_id)
   └─ Log stdout/stderr to .logs/

3. Health Check
   └─ Poll port every 0.5s for up to 10 seconds
   └─ If port never opens: read stderr, go to Repair

4. Success
   └─ Mark run as "success"
   └─ Return preview URL

── Repair Sub-loop ──────────────────────────────────────────
1. Extract traceback from stderr log
2. Build context: gather relevant file contents (up to 4000 chars each)
3. Call repair_model LLM with error + context
4. Parse LLM response as unified diff patch
5. Apply patch to workspace files
6. Re-run post-processing (route injection, import checks)
7. Increment attempt counter, retry from Syntax Check
─────────────────────────────────────────────────────────────
```

If all repair attempts are exhausted, the run is marked as `"failed"` with the final error logged.

---

## 8. Module-Level Design

### 8.1 Orchestrator (`orchestrator.py`)

The orchestrator is the central controller. It:
- Creates `Project` and `Run` database records.
- Emits structured `LogEvent` records at each stage (stage name, level, message).
- Coordinates all service calls sequentially.
- Exposes two public async methods:
  - `execute_run(project_id, run_id, user_prompt)` — Full generation pipeline.
  - `execute_modification(project_id, run_id, user_request)` — Feedback/modification pipeline.

### 8.2 LLM Clients

**OllamaLLM** (`llm/providers/ollama_client.py`)
- Calls `POST /api/chat` on the local Ollama server.
- Handles streaming responses.
- Timeout: 1200 seconds.
- Converts system/user prompt to Ollama messages format.

**OpenAICompatLLM** (`llm/providers/openai_compat_client.py`)
- Calls `POST /v1/chat/completions` on any OpenAI-compatible endpoint.
- Bearer token authentication.
- Temperature: 0.2 (near-deterministic for code generation).
- Compatible with: Claude API, Azure OpenAI, Groq, local vLLM, etc.

### 8.3 Patcher (`patcher.py`)

The patcher is responsible for safely applying LLM-generated patches to files on disk. It implements a **four-tier fallback strategy**:

1. **Git/Unified diff** (`diff --git`, `@@` hunks) — standard diff format.
2. **`*** Begin Patch` / `*** End Patch` format** — custom patch format with `+++ REPLACE ENTIRE FILE +++` support.
3. **JSON `{"files": [...]}` format** — direct file replacement via JSON array.
4. **Error** — if all three fail, an error is raised and the run is marked failed.

Pre-processing steps before parsing:
- Strip markdown code fences (` ```patch `, ` ```diff `, etc.).
- Normalise marker variations (`** Begin` → `*** Begin`).
- Remove `<think>` / `</think>` tags from model chain-of-thought output.

### 8.4 Workspace Manager (`workspace.py`)

Provides two core functions:
- `project_workspace(project_id, run_id) → Path` — Returns (and creates if absent) the workspace directory for a specific run.
- `write_files(workspace, files) → None` — Batch-writes a list of `{path, content}` objects to disk, creating intermediate directories as needed.

---

## 9. Database Design

The system uses a SQLite database managed through SQLModel (a thin ORM combining SQLAlchemy and Pydantic).

### 9.1 Entity-Relationship Overview

```
Project ──< Run ──< LogEvent
```

### 9.2 Tables

#### `project`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK) | Auto-increment primary key |
| `name` | TEXT | Project name |
| `created_at` | DATETIME | Creation timestamp |

#### `run`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK) | Auto-increment primary key |
| `project_id` | INTEGER (FK → project.id) | Parent project |
| `status` | TEXT | `queued` / `running` / `success` / `failed` |
| `entrypoint` | TEXT | Backend entry point filename (default: `main.py`) |
| `attempts` | INTEGER | Number of repair attempts made |
| `created_at` | DATETIME | Creation timestamp |

#### `logevent`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK) | Auto-increment primary key |
| `run_id` | INTEGER (FK → run.id, indexed) | Parent run |
| `stage` | TEXT | Pipeline stage (`enhance`, `spec`, `codegen`, `deps`, `run`, `repair`) |
| `level` | TEXT | `INFO` / `WARN` / `ERROR` |
| `message` | TEXT | Human-readable log message |
| `created_at` | DATETIME | Timestamp |

### 9.3 API Endpoints Backed by These Models

| Method | Endpoint | Function |
|--------|----------|----------|
| POST | `/projects` | Create a new project |
| GET | `/projects` | List all projects |
| POST | `/projects/{project_id}/runs` | Start a generation run (background task) |
| GET | `/runs/{run_id}` | Get run status and metadata |
| GET | `/runs/{run_id}/logs` | Stream log events (SSE or polling) |
| GET | `/projects/{project_id}/runs/{run_id}/files` | Browse generated file tree |
| GET | `/projects/{project_id}/runs/{run_id}/files/{path}` | Read a specific generated file |
| GET | `/projects/{project_id}/runs/{run_id}/download` | Download generated app as ZIP |
| POST | `/projects/{project_id}/runs/{run_id}/modify` | Request a modification (background task) |

---

## 10. Fine-Tuning Methodology

### 10.1 Base Model Selection

**Model:** `Qwen/Qwen2.5-Coder-3B-Instruct`

**Rationale:**
- 3 billion parameters: small enough to run on a single consumer GPU (≥8 GB VRAM) or quantized on CPU, yet capable enough for structured JSON and code generation.
- Coder-specialised: pre-trained on code corpora, giving a strong starting point for code generation tasks.
- Instruction-tuned: follows system/user/assistant chat format natively, reducing the prompt engineering burden.

### 10.2 Fine-Tuning Technique: LoRA (Low-Rank Adaptation)

**Why LoRA:**
Full fine-tuning of a 3B model requires significant VRAM and storage. LoRA instead inserts small, trainable rank-decomposition matrices into the attention layers of the frozen base model. This reduces trainable parameters by ~100× while retaining most of the performance benefit.

**Configuration:**

| Parameter | Value |
|-----------|-------|
| LoRA Rank (r) | 16 |
| LoRA Alpha | 32 |
| Target Modules | `q_proj`, `v_proj` |
| Dropout | 0.05 |
| Quantization | 4-bit NF4 (BitsAndBytes) |
| Double Quantization | Enabled |

### 10.3 Training Configuration

| Parameter | Value |
|-----------|-------|
| Trainer | Hugging Face TRL `SFTTrainer` |
| Epochs | 30 |
| Batch Size | 1 |
| Gradient Accumulation Steps | 4 (effective batch = 4) |
| Learning Rate | 1e-4 |
| LR Scheduler | Cosine |
| Max Sequence Length | 1024 tokens |
| Gradient Checkpointing | Enabled |
| Logging Interval | Every 10 steps |
| Eval Interval | Every 50 steps |
| Checkpoint Save Interval | Every 50 steps |
| Best Model Metric | Validation loss |

### 10.4 Fine-Tuning Variants

Three distinct LoRA adapters are trained, one per pipeline role:

#### Variant 1: TaskSpec LoRA (`train_taskspec_only.py`)
- **Goal:** Reliable, schema-conformant TaskSpec JSON generation.
- **Training Data:** `fine_tune_dataset/taskspec_only/{train,val}.jsonl`
- **Output Dir:** `finetune/outputs/qwen_taskspec_only_lora`
- **Data Format:**
  ```json
  {
    "messages": [
      {"role": "system",    "content": "You are a senior software architect..."},
      {"role": "user",      "content": "Create a TaskSpec for: recipe sharing platform"},
      {"role": "assistant", "content": "{\"app_name\": \"RecipeHub\", ...}"}
    ]
  }
  ```

#### Variant 2: Coder LoRA (`train_coder_model.py`)
- **Goal:** Generate complete, multi-file web application code from a TaskSpec.
- **Training Data:** `fine_tune_dataset/code/{train,val}.jsonl`
- **Input:** TaskSpec JSON.
- **Output:** `GenOutput` JSON with file paths and contents.

#### Variant 3: Repair LoRA (`train_taskspec_repair.py`)
- **Goal:** Generate correct patches in response to Python runtime error tracebacks.
- **Training Data:** Error-patch pairs derived from failed generation runs.
- **Input:** Error traceback + relevant file snippets.
- **Output:** Unified diff patch or `*** Begin Patch` format.

### 10.5 Dataset Construction

Training data is constructed from three sources:
1. **Synthetically generated examples:** An existing capable LLM (e.g., GPT-4 or Claude) is prompted to generate TaskSpec / GenOutput pairs for a diverse set of application types.
2. **Real pipeline outputs:** Successful runs of the system are harvested, reviewed, and added to training data.
3. **Cleaned JSON datasets:** The `Cleaned-Json/` and `Cleaned-Json2/` directories contain processed JSON samples used for spec training.

The `finetune/scripts/` directory contains:
- `MASTER_TRAINING_DATA.json` — Merged master dataset.
- `Code-finetuning-dataset.json` — Code generation training pairs.
- `extract_clean_json.py` — Data cleaning and validation scripts.

---

## 11. Sandbox & Isolation Strategy

### 11.1 Why Isolation Matters

Each generated application is a standalone FastAPI server. Without isolation:
- Package conflicts between runs could cause failures.
- A buggy generated app could crash or poison the host environment.
- Port conflicts would prevent multiple simultaneous previews.

### 11.2 VenvSandboxRunner Design

The `VenvSandboxRunner` class manages the full lifecycle of a generated app's execution environment:

```
┌─────────────────────────────────────────────────┐
│            VenvSandboxRunner                     │
│                                                  │
│  setup()        → python -m venv .venv_sandbox   │
│                 → pip install fastapi uvicorn ... │
│                                                  │
│  install_deps() → pip install -r requirements.txt│
│                                                  │
│  check_syntax() → python -m py_compile *.py      │
│                                                  │
│  run_uvicorn()  → spawn uvicorn subprocess       │
│                 → bind to port (8010 + run_id)   │
│                 → redirect logs to .logs/        │
│                                                  │
│  stop_uvicorn() → terminate → kill (if needed)   │
└─────────────────────────────────────────────────┘
```

### 11.3 Port Allocation Strategy

Generated apps are served on dynamically allocated ports:

```
Preview Port = PREVIEW_PORT_BASE + run_id
             = 8010 + run_id
```

This guarantees no two runs share a port. The frontend embeds the generated app in an `<iframe>` pointing to `http://localhost:{port}`.

### 11.4 Process Lifecycle

- Uvicorn is spawned as a subprocess with its stdout and stderr redirected to log files.
- A process handle registry (keyed by `run_id`) allows clean shutdown.
- On `stop_uvicorn_for_run(run_id)`: `terminate()` is called first; if the process persists after a grace period, `kill()` is used.

---

## 12. Frontend Architecture

### 12.1 Page Structure

| Route | Purpose |
|-------|---------|
| `/` | Landing page — project overview and "Get Started" entry point |
| `/describe` | Prompt input form — user enters their application description |
| `/generating` | Generation progress view — real-time log streaming, stage progress |
| `/ide` | IDE view — file tree browser, code viewer, modification request form |
| `/preview` | Fullscreen iframe preview of the generated running application |
| `/about` | About page |

### 12.2 Key Frontend Components

- **Log Streamer:** Polls `GET /runs/{run_id}/logs` and renders stage-by-stage progress in real time.
- **File Tree:** Hierarchical display of the generated app's file structure.
- **Code Viewer:** Syntax-highlighted display of individual file contents.
- **Preview Iframe:** Embeds the live generated application at its dynamic port.
- **Modification Form:** Text input for submitting post-generation change requests in plain English.

### 12.3 API Communication

The frontend communicates with the backend via:

```
NEXT_PUBLIC_API_URL=http://localhost:8002
```

All API calls use the native Fetch API. Background polling is used for run status and log updates, with a configurable polling interval.

---

## 13. Modification & Feedback Loop

After a successful generation, users can request changes in plain English (e.g., *"Make the navbar dark blue"*, *"Add a contact form to the homepage"*).

### 13.1 Modification Pipeline

```
User Request (plain English)
        │
        ▼
[Phase 0] Feedback Enhancement
        │  prompt_enhancer.py
        │  "make navbar blue" → "Set the navbar background-color to #1E3A8A"
        │
        ▼
[Phase 1] Planner (modifier.py: llm_plan_modification)
        │  LLM identifies which files need to change
        │  Output: { "modify": ["frontend/index.html", ...], "reason": "..." }
        │
        ▼
[Phase 2] Editor (modifier.py: llm_targeted_modify)
        │  LLM receives target file contents + request
        │  Output: Patch (*** Begin Patch format) or JSON files[]
        │
        ▼
[Phase 3] Patcher (patcher.py: apply_unified_patch)
        │  Applies patch to workspace files
        │
        ▼
[Phase 4] Verification
        │  Syntax check → Restart Uvicorn → Check port
        │
        ▼
Status: success | failed
```

### 13.2 Patch Formats Supported

The system supports two output formats from the modification LLM:

**Format A — Custom Patch Format (preferred):**
```
*** Begin Patch
*** Update File: generated_app/frontend/index.html
+++ REPLACE ENTIRE FILE +++
<!DOCTYPE html>
... (full new file content) ...
*** End Patch
```

**Format B — JSON File Replacement:**
```json
{
  "files": [
    {
      "path": "generated_app/frontend/index.html",
      "content": "<!DOCTYPE html>..."
    }
  ]
}
```

---

## 14. Deployment & Infrastructure

### 14.1 Docker Compose Architecture

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8002:8002"         # FastAPI API
      - "8010-8110:8010-8110"  # Generated app previews
    volumes:
      - ./storage:/app/storage   # SQLite DB + workspaces
    environment:
      - DATABASE_URL=sqlite:///./app.db
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - LLM_MODE=ollama

  frontend:
    build: ./frontend
    ports:
      - "3001:3001"         # Next.js UI
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8002
```

### 14.2 Environment Configuration

All system behaviour is controlled through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./app.db` | Database connection string |
| `LLM_MODE` | `ollama` | `ollama` or `api` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `API_BASE_URL` | — | OpenAI-compatible endpoint URL |
| `API_KEY` | — | API key for OpenAI-compatible provider |
| `MODEL_SPEC` | — | Model name for spec generation |
| `MODEL_CODE` | — | Model name for code generation |
| `MODEL_REPAIR` | — | Model name for error repair |
| `MODEL_ENHANCE` | `qwen2.5:7b-instruct` | Model for prompt enhancement |
| `MAX_REPAIR_ATTEMPTS` | `2` | Maximum auto-repair iterations |
| `PREVIEW_PORT_BASE` | `8010` | Base port for generated app previews |

### 14.3 Workspace File Structure

Every generation run produces the following directory structure:

```
storage/workspaces/
└── project_{id}/
    └── run_{id}/
        ├── generated_app/
        │   ├── frontend/
        │   │   ├── index.html
        │   │   ├── about.html
        │   │   ├── contact.html
        │   │   └── main.css
        │   └── backend/
        │       ├── main.py
        │       └── requirements.txt
        ├── .venv_sandbox/          ← Isolated Python venv
        ├── .logs/
        │   ├── uvicorn.stdout.log
        │   └── uvicorn.stderr.log
        └── project_download.zip    ← User-downloadable archive
```

---

## 15. Data Flow Diagrams

### 15.1 Generation Pipeline (Full Flow)

```
┌──────────┐     HTTP POST /runs       ┌────────────────────┐
│ Browser  │ ─────────────────────────▶│  FastAPI Backend   │
│(Next.js) │                           │  (routes/runs.py)  │
└──────────┘                           └────────┬───────────┘
     ▲                                          │ background task
     │ SSE/Poll logs                            ▼
     │                                 ┌────────────────────┐
     │                                 │   Orchestrator     │
     │                                 │  execute_run()     │
     │                                 └──────┬─────────────┘
     │                        ┌──────────────▼──────────────┐
     │                        │         Stage 0             │
     │                        │    prompt_enhancer.py       │
     │                        │  LLM: enhance_model         │
     │                        └──────────────┬──────────────┘
     │                        ┌──────────────▼──────────────┐
     │                        │         Stage 1             │
     │                        │    spec_generator.py        │
     │                        │  LLM: spec_model            │
     │                        │  Output: TaskSpec JSON      │
     │                        └──────────────┬──────────────┘
     │                        ┌──────────────▼──────────────┐
     │                        │         Stage 2             │
     │                        │    code_generator.py        │
     │                        │  LLM: code_model            │
     │                        │  Output: GenOutput (files)  │
     │                        └──────────────┬──────────────┘
     │                        ┌──────────────▼──────────────┐
     │                        │         Stage 3             │
     │                        │    Validation (non-blocking) │
     │                        └──────────────┬──────────────┘
     │                        ┌──────────────▼──────────────┐
     │                        │       Stages 4–5            │
     │                        │  VenvSandboxRunner          │
     │                        │  setup() + install_deps()   │
     │                        └──────────────┬──────────────┘
     │                        ┌──────────────▼──────────────┐
     │                        │         Stage 6             │
     │                        │    Run + Repair Loop        │
     │                        │  ┌────────────────────────┐ │
     │                        │  │ syntax_check           │ │
     │                        │  │ run_uvicorn()          │ │
     │                        │  │ health_check()         │ │
     │                        │  │  ╔══ if fail ═════╗    │ │
     │                        │  │  ║ extract_error  ║    │ │
     │                        │  │  ║ llm_repair()   ║    │ │
     │                        │  │  ║ apply_patch()  ║    │ │
     │                        │  │  ╚════════════════╝    │ │
     │                        │  └────────────────────────┘ │
     │                        └──────────────┬──────────────┘
     │                                       │
     │              run.status = "success"   │
     └───────────────────────────────────────┘
         (preview URL: http://localhost:8010+run_id)
```

### 15.2 LLM Call Chain

```
User Prompt
    │
    ▼  [LLM 1: enhance_model (Qwen 7B general)]
Enhanced Prompt
    │
    ▼  [LLM 2: spec_model (Qwen 3B, TaskSpec LoRA)]
TaskSpec JSON
    │
    ▼  [LLM 3: code_model (Qwen 3B, Coder LoRA)]
GenOutput (HTML + CSS + JS + Python files)
    │
    ▼  [if error during run]
    │  [LLM 4: repair_model (Qwen 3B, Repair LoRA)]
Patch
    │
    ▼  [if user requests modification]
    │  [LLM 5: code_model (same as LLM 3)]
Modification Patch
```

---

## 16. Evaluation & Quality Gates

### 16.1 Automated Quality Checks (Stage 3)

| Check | Rule | Severity |
|-------|------|----------|
| No Lorem ipsum | `"lorem ipsum"` not in HTML (case-insensitive) | WARNING |
| No generic placeholders | Patterns like `Feature [0-9]`, `Service N` not in HTML | WARNING |
| CSS minimum length | ≥ 50 lines | WARNING |
| JS minimum length | ≥ 30 lines | WARNING |
| Backend route presence | At least one `@app.get(` in `main.py` | WARNING |
| FileResponse import | `from fastapi.responses import FileResponse` in `main.py` | WARNING |

### 16.2 Runtime Health Check

After starting Uvicorn, the system polls the allocated port every 500ms for up to 10 seconds. If the port becomes active, the application is considered healthy. If Uvicorn crashes before the port opens, the stderr log is read to extract the error for the repair loop.

### 16.3 Syntax Validation

Before each Uvicorn start (including after patches), all `.py` files in the generated workspace are validated with `python -m py_compile`. Any syntax error surfaces immediately without needing to start the server.

---

## 17. Limitations & Future Work

### 17.1 Current Limitations

| Area | Limitation |
|------|-----------|
| **Model size** | Qwen-3B may produce shallow architectures for complex apps |
| **Context window** | Training was limited to 1024 tokens; long files may be truncated during repair |
| **Repair attempts** | Only 2 repair attempts; complex cascading errors may not be resolved |
| **Modification fragility** | Patch format ambiguity from LLM output causes silent failures |
| **No rollback** | Partial patch application leaves files in inconsistent state |
| **HTML/CSS quality** | Min-line checks are heuristic, not semantic |
| **No auth/security** | Generated apps have no authentication or input sanitisation |
| **Single-language** | Only generates Python/FastAPI backends; no Node.js, Django, etc. |

### 17.2 Planned / Future Improvements

1. **Atomic patch transactions:** Stage modified files to a temp directory, validate, then commit — with rollback on failure.
2. **Larger context repair:** Use sliding window or file summarisation to handle large files in the repair context.
3. **Semantic HTML validation:** Parse the DOM and validate that all referenced CSS classes and JS functions exist.
4. **Multi-framework support:** Extend to generate Django, Express.js, or Spring Boot backends.
5. **Human-curated training data:** Replace synthetic training data with human-reviewed golden examples.
6. **Continuous learning:** Collect failed → repaired pairs from production to continuously improve the repair model.
7. **Streaming code generation:** Stream generated file contents to the frontend in real time rather than waiting for the full generation.
8. **User authentication:** Add user accounts so multiple users can manage separate projects.

---

## Appendix A — Key File Reference

| File | Purpose |
|------|---------|
| [backend/app/services/orchestrator.py](backend/app/services/orchestrator.py) | Master pipeline controller |
| [backend/app/services/prompt_enhancer.py](backend/app/services/prompt_enhancer.py) | Stage 0: Prompt enrichment |
| [backend/app/services/spec_generator.py](backend/app/services/spec_generator.py) | Stage 1: TaskSpec generation |
| [backend/app/services/code_generator.py](backend/app/services/code_generator.py) | Stage 2: Code generation |
| [backend/app/services/modifier.py](backend/app/services/modifier.py) | Post-gen modification |
| [backend/app/patcher.py](backend/app/patcher.py) | Patch parsing & application |
| [backend/app/sandbox/venv_runner.py](backend/app/sandbox/venv_runner.py) | Isolated venv execution |
| [backend/app/llm/router.py](backend/app/llm/router.py) | LLM model routing |
| [backend/app/core/config.py](backend/app/core/config.py) | Environment configuration |
| [backend/app/core/utils.py](backend/app/core/utils.py) | JSON repair, traceback parsing |
| [backend/app/workspace.py](backend/app/workspace.py) | File I/O and workspace management |
| [finetune/scripts/](finetune/scripts/) | Fine-tuning training scripts and datasets |

---

## Appendix B — Glossary

| Term | Definition |
|------|-----------|
| **TaskSpec** | Structured JSON object defining the app's architecture: pages, API endpoints, data models, and styling |
| **GenOutput** | Structured JSON object containing all generated source files (paths + contents) |
| **GenFile** | A single generated file with `path` and `content` fields |
| **LoRA** | Low-Rank Adaptation — efficient fine-tuning technique that adds small trainable matrices to a frozen base model |
| **Venv Sandbox** | Isolated Python virtual environment created per run to prevent dependency conflicts |
| **Repair Loop** | Automated cycle of error extraction → LLM patch generation → patch application → retry |
| **Patcher** | Module responsible for parsing LLM-generated patches and safely writing changes to disk |
| **LLM Mode** | System configuration: `ollama` (local) or `api` (cloud/remote OpenAI-compatible) |
| **Entrypoint** | The main Python file of the generated backend (typically `backend/main.py`) |
| **Run** | A single generation attempt associated with a project, tracked in the database with status and logs |

---

*Document prepared for academic submission — FYP Project: Prompt2Product*
*Generated from source code analysis of the d:/FYP repository*
