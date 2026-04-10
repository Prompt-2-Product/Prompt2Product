"""
modifier.py — Robust Modification Pipeline for Prompt2Product
=============================================================
Strategy:
  - Planner returns a strict, validated JSON structure (with fallback key aliases).
  - Editor is prompted to return FULL file rewrites OR annotated hunks.
  - All LLM output is sanitized before parsing (strip markdown fences, normalize whitespace).
  - Every modification attempt is logged with a clear success/failure status.
"""

import json
import re
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json, ```python, ``` etc. that LLMs love to add."""
    # Remove opening fence (with optional language tag) and closing fence
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\n?```$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()


def _extract_json_from_text(text: str) -> dict:
    """
    Robustly extract JSON from LLM output that may contain prose around it.
    Tries in order:
      1. Direct parse after stripping fences.
      2. Regex extraction of the first {...} block.
      3. Raises ValueError if nothing works.
    """
    # Attempt 1: clean and parse directly
    cleaned = _strip_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 2: find the first JSON object in the string
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from LLM output:\n{text[:500]}")


def _normalize_planner_output(raw: dict) -> list[str]:
    """
    Accept multiple plausible key names the LLM might use for the file list.
    Returns a list of file path strings.
    """
    candidate_keys = ["modify", "files", "file_list", "targets", "changed_files", "edit"]
    for key in candidate_keys:
        if key in raw:
            val = raw[key]
            if isinstance(val, list):
                return [str(f) for f in val]
            if isinstance(val, str):
                return [val]  # single file as string
    raise ValueError(f"Planner JSON missing a recognized file list key. Got keys: {list(raw.keys())}")


# ---------------------------------------------------------------------------
# Phase 1 — Planner
# ---------------------------------------------------------------------------

PLANNER_SYSTEM_PROMPT = """
You are a senior software architect analyzing a codebase to plan a minimal, targeted code change.

You will receive:
- A user feedback request (what they want changed)
- The project file tree

Your job: decide which files need to be modified to fulfill the request.

RULES:
- Respond ONLY with a raw JSON object. No markdown, no explanation, no code fences.
- Use exactly this schema:
  {"modify": ["path/to/file.html", "path/to/file.css"], "reason": "one sentence why"}
- Only include files that genuinely need changes. Less is more.
- File paths must match exactly what was given in the file tree.
""".strip()


def build_planner_prompt(enhanced_feedback: str, file_tree: str) -> str:
    return f"""User request: {enhanced_feedback}

Project file tree:
{file_tree}

Which files need to be modified? Respond with JSON only."""


def parse_planner_response(raw_text: str) -> tuple[list[str], str]:
    """
    Parse planner LLM response.
    Returns (list_of_files_to_modify, reason_string).
    Never raises — returns empty list + error string on failure.
    """
    try:
        data = _extract_json_from_text(raw_text)
        files = _normalize_planner_output(data)
        reason = data.get("reason", data.get("explanation", "No reason provided"))
        logger.info(f"[Planner] Will modify {len(files)} file(s): {files}")
        return files, reason
    except (ValueError, KeyError) as e:
        logger.error(f"[Planner] Failed to parse response: {e}")
        return [], f"Parse error: {e}"


# ---------------------------------------------------------------------------
# Phase 2 — Editor
# ---------------------------------------------------------------------------

# The editor is given two strategy options based on change scope:
#   - HUNK mode: for small targeted changes (1–20 lines affected)
#   - FULL_REWRITE mode: for structural changes or when hunk might fail

EDITOR_SYSTEM_PROMPT_HUNK = """
You are an expert code editor making a precise, minimal change to a source file.

You will receive:
- A modification instruction
- The full current content of the file

Your output MUST follow this EXACT format and nothing else:

<<<HUNK_START>>>
SEARCH:
<exact lines to find — must match the file content character-for-character including indentation>
REPLACE:
<new lines to substitute in — same indentation style as surrounding code>
<<<HUNK_END>>>

CRITICAL RULES:
1. Do NOT wrap output in markdown code fences.
2. The SEARCH block must be unique enough to locate the right position (use 3–5 lines of context).
3. Preserve ALL indentation exactly. Tabs stay tabs, spaces stay spaces.
4. You may emit multiple HUNK blocks if you need to change multiple locations in the same file.
5. If you are not 100% confident the SEARCH text exists verbatim in the file, use FULL_REWRITE instead.
""".strip()

EDITOR_SYSTEM_PROMPT_FULL_REWRITE = """
You are an expert code editor rewriting a source file to implement a requested change.

You will receive:
- A modification instruction
- The full current content of the file

Your output MUST be:
<<<REWRITE_START>>>
<complete new file content — every single line, nothing omitted>
<<<REWRITE_END>>>

CRITICAL RULES:
1. Output the ENTIRE file, not just the changed section.
2. Do NOT add any explanation before or after the markers.
3. Do NOT wrap in markdown fences.
4. Preserve all existing functionality. Only change what the instruction requires.
""".strip()


def build_editor_prompt(instruction: str, filename: str, file_content: str, mode: str = "hunk") -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for the editor LLM call.
    mode: "hunk" | "full_rewrite"
    """
    system = EDITOR_SYSTEM_PROMPT_HUNK if mode == "hunk" else EDITOR_SYSTEM_PROMPT_FULL_REWRITE

    user = f"""Modification instruction: {instruction}

File: {filename}
Current content:
---
{file_content}
---

Apply the change now."""
    return system, user


def parse_editor_response(raw_text: str) -> dict[str, Any]:
    """
    Parse editor LLM response.
    Returns a dict:
      {
        "mode": "hunk" | "full_rewrite" | "unknown",
        "hunks": [{"search": str, "replace": str}, ...],  # for hunk mode
        "full_content": str,                               # for full_rewrite mode
        "raw": str
      }
    """
    # Strip stray markdown fences first
    text = _strip_markdown_fences(raw_text)

    # --- Detect FULL REWRITE ---
    rewrite_match = re.search(
        r"<<<REWRITE_START>>>\n?(.*?)\n?<<<REWRITE_END>>>",
        text,
        re.DOTALL,
    )
    if rewrite_match:
        return {
            "mode": "full_rewrite",
            "full_content": rewrite_match.group(1),
            "hunks": [],
            "raw": raw_text,
        }

    # --- Detect HUNKS ---
    hunk_blocks = re.findall(
        r"<<<HUNK_START>>>\n?SEARCH:\n(.*?)\nREPLACE:\n(.*?)\n?<<<HUNK_END>>>",
        text,
        re.DOTALL,
    )
    if hunk_blocks:
        hunks = [{"search": s, "replace": r} for s, r in hunk_blocks]
        logger.info(f"[Editor] Parsed {len(hunks)} hunk(s)")
        return {
            "mode": "hunk",
            "hunks": hunks,
            "full_content": "",
            "raw": raw_text,
        }

    # --- Fallback: legacy SEARCH/REPLACE format (backward compat) ---
    legacy_blocks = re.findall(
        r"SEARCH:\n(.*?)\nREPLACE:\n(.*?)(?=\nSEARCH:|\Z)",
        text,
        re.DOTALL,
    )
    if legacy_blocks:
        logger.warning("[Editor] Fell back to legacy SEARCH/REPLACE parser")
        hunks = [{"search": s.strip(), "replace": r.strip()} for s, r in legacy_blocks]
        return {
            "mode": "hunk",
            "hunks": hunks,
            "full_content": "",
            "raw": raw_text,
        }

    logger.error("[Editor] Could not parse any hunk or rewrite blocks from LLM output")
    return {
        "mode": "unknown",
        "hunks": [],
        "full_content": "",
        "raw": raw_text,
    }
