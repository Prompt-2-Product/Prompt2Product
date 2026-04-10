import json
import re
from pathlib import Path
from app.core.utils import clean_requirements_text, extract_balanced_json_object, extract_json, repair_json
from app.services.git_diff_apply import try_apply_git_unified_diff

PATCH_BEGIN = "*** Begin Patch"
PATCH_END = "*** End Patch"


def _slice_balanced_braces(text: str, start_idx: int) -> str | None:
    if start_idx < 0 or start_idx >= len(text) or text[start_idx] != "{":
        return None
    depth = 0
    in_str = False
    esc = False
    for j in range(start_idx, len(text)):
        c = text[j]
        if esc:
            esc = False
            continue
        if c == "\\" and in_str:
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if not in_str:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start_idx : j + 1]
    return None


def _extract_best_fence_block(text: str) -> str:
    """Pull patch/JSON out of ``` ... ``` when the model wraps it in prose."""
    blocks = re.findall(r"```(?:[\w+-]+)?\s*([\s\S]*?)```", text, flags=re.I)
    if not blocks:
        return text

    def heuristic_score(b: str) -> tuple[int, int]:
        b = b.strip()
        score = 0
        if "Update File" in b or "*** Update File" in b:
            score += 12
        if PATCH_BEGIN in b or "*** Begin" in b:
            score += 8
        if '"files"' in b or "'files'" in b:
            score += 12
        if "generated_app/" in b:
            score += 4
        if "+++" in b and "REPLACE" in b.upper():
            score += 6
        if "diff --git" in b:
            score += 10
        if "@@" in b:
            score += 5
        return (score, len(b))

    best = max(blocks, key=heuristic_score)
    if heuristic_score(best)[0] > 0:
        return best.strip()
    return text


def _strip_llm_noise(text: str) -> str:
    text = text.strip()
    text = re.sub(r"<[^>]*thinking[^>]*>[\s\S]*?</[^>]*thinking[^>]*>", "", text, flags=re.I)
    # Outer markdown fences only (avoid eating ``` inside HTML)
    text = re.sub(r"^```(?:patch|diff|json|text|plaintext)?\s*\n?", "", text.strip(), flags=re.I)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.I)
    return text.strip()


def _normalize_patch_markers(text: str) -> str:
    """Map common LLM variants onto the strict *** Begin / *** Update File format."""
    t = text.replace("\r\n", "\n")

    # Case-insensitive Begin/End patch lines
    t = re.sub(r"(?mi)^\*{2,3}\s*Begin\s+Patch\s*$", PATCH_BEGIN, t)
    t = re.sub(r"(?mi)^\*{2,3}\s*End\s+Patch\s*$", PATCH_END, t)

    # ** Update File: or * Update File:  ->  *** Update File:
    t = re.sub(r"(?m)^\*\*\s+Update File:\s*", "*** Update File: ", t, flags=re.I)
    t = re.sub(r"(?m)^\*\s+Update File:\s*", "*** Update File: ", t, flags=re.I)
    # ### Update File:
    t = re.sub(r"(?m)^#+\s*Update File:\s*", "*** Update File: ", t, flags=re.I)
    # "Update File: path" at line start without asterisks
    t = re.sub(r"(?m)^(Update File:\s+)", r"*** \1", t, flags=re.I)

    # Inconsistent asterisk count before Update File (2+ stars), any case
    t = re.sub(r"(?m)^\*{2,3}\s*Update\s+File\s*:\s*", "*** Update File: ", t, flags=re.I)

    # Inline "***Update File:" (no space after stars) — rare
    t = re.sub(r"\*\*\*\s*Update\s+File\s*:\s*", "*** Update File: ", t, flags=re.I)

    # Lines that are only "File: relative/path" (some models use this)
    out_lines: list[str] = []
    for line in t.split("\n"):
        m = re.match(r"(?i)^(?:File|Path)\s*:\s*(.+)$", line.strip())
        if m and "generated_app" in m.group(1):
            out_lines.append("*** Update File: " + m.group(1).strip())
        else:
            out_lines.append(line)
    t = "\n".join(out_lines)

    if re.search(r"(?mi)^\*\*\*\s*Update File:", t) and PATCH_BEGIN not in t:
        t = PATCH_BEGIN + "\n" + t
    if re.search(r"(?mi)^\*\*\*\s*Update File:", t) and PATCH_END not in t:
        t = t.rstrip() + "\n" + PATCH_END

    return t.strip()


def _merge_diff_fence_blocks(text: str) -> str:
    """Concatenate all markdown diff/patch fences so multi-block LLM replies still apply."""
    blocks = re.findall(r"```(?:diff|patch)?\s*\n?([\s\S]*?)```", text, flags=re.I)
    useful: list[str] = []
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        head = "\n".join(b.split("\n")[:8])
        if "@@" in b or "diff --git" in b or (b.startswith("---") and "+++" in head):
            useful.append(b)
    return "\n\n".join(useful)


def _json_blob_candidates(text: str) -> list[str]:
    blobs: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            blobs.append(s)

    if re.search(r'"files"\s*:', text) or re.search(r"'files'\s*:", text):
        ej = extract_json(text)
        if ej:
            add(ej)
        bal = extract_balanced_json_object(text, required_substrings=('"files"',))
        if bal:
            add(bal)
        bal2 = extract_balanced_json_object(text, required_substrings=())
        if bal2 and '"files"' in bal2:
            add(bal2)

    # Balanced object starting at {"files" ...} (avoids scanning every { in HTML/CSS)
    for m in re.finditer(r"\{\s*\"files\"\s*:", text):
        frag = _slice_balanced_braces(text, m.start())
        if frag and len(frag) >= 25:
            add(frag)

    return blobs


def _try_json_files_patch(workspace: Path, text: str) -> int:
    """If the model returned JSON { \"files\": [{\"path\", \"content\"}, ...] }, apply it."""
    parsed: dict | None = None
    for raw in _json_blob_candidates(text):
        for use_repair in (False, True):
            try:
                blob = repair_json(raw) if use_repair else raw
                candidate = json.loads(blob)
                if isinstance(candidate, dict) and isinstance(candidate.get("files"), list):
                    parsed = candidate
                    break
            except json.JSONDecodeError:
                continue
        if parsed is not None:
            break
    if parsed is None:
        return 0
    files = parsed.get("files")
    if not isinstance(files, list):
        return 0
    count = 0
    for item in files:
        if not isinstance(item, dict):
            continue
        rel = item.get("path") or item.get("file")
        content = item.get("content")
        if rel is None or content is None:
            continue
        rel = str(rel).strip().strip("`").replace("\\", "/")
        if not rel:
            continue
        new_content = content if isinstance(content, str) else json.dumps(content)
        file_abs = (workspace / rel).resolve()
        file_abs.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("requirements.txt"):
            new_content = clean_requirements_text(new_content)
        file_abs.write_text(new_content if new_content.endswith("\n") else new_content + "\n", encoding="utf-8")
        count += 1
    return count


def apply_unified_patch(workspace: Path, patch_text: str) -> None:
    """
    Supports patches in the format:
    *** Begin Patch
    *** Update File: path/to/file
    +++ REPLACE ENTIRE FILE +++
    new content
    *** End Patch

    Also accepts common LLM variants (fewer asterisks, missing Begin/End), JSON {files: [...]},
    and git/unified diffs (diff --git / @@ hunks) inside or outside markdown fences.
    """
    raw = patch_text
    merged_diff = _merge_diff_fence_blocks(raw)
    for candidate in (merged_diff, _strip_llm_noise(raw)):
        if candidate.strip() and try_apply_git_unified_diff(workspace, candidate) > 0:
            return

    patch_text = _extract_best_fence_block(raw)
    patch_text = _strip_llm_noise(patch_text)
    if patch_text.strip() and try_apply_git_unified_diff(workspace, patch_text) > 0:
        return

    patch_text = _normalize_patch_markers(patch_text)

    # Lenient check: need either strict Update File blocks or JSON files[]
    has_update = "*** Update File:" in patch_text
    has_begin = PATCH_BEGIN in patch_text
    if not has_update:
        if _try_json_files_patch(workspace, patch_text):
            return
        if _try_json_files_patch(workspace, raw):
            return
        if not has_begin:
            raise ValueError("Patch missing Begin/End markers and no file updates found")

    # Split into file blocks
    blocks = re.split(r"\*\*\* Update File:\s*", patch_text)

    wrote = 0
    for b in blocks[1:]:
        if not b.strip():
            continue

        lines = b.splitlines()
        file_path = lines[0].strip().strip("`").strip()
        content_lines = lines[1:]
        if content_lines and PATCH_END in content_lines[-1]:
            content_lines[-1] = content_lines[-1].replace(PATCH_END, "").strip()
            if not content_lines[-1]:
                content_lines.pop()

        file_abs = (workspace / file_path).resolve()
        if not file_abs.exists():
            file_abs.parent.mkdir(parents=True, exist_ok=True)

        new_content = ""
        if any(ln.startswith("+++ REPLACE ENTIRE FILE +++") for ln in content_lines):
            idx = next(i for i, ln in enumerate(content_lines) if ln.startswith("+++ REPLACE ENTIRE FILE +++"))
            new_content = "\n".join(content_lines[idx + 1 :]) + "\n"
        else:
            clean_lines = [ln for ln in content_lines if not ln.startswith("***")]
            new_content = "\n".join(clean_lines) + "\n"

        if file_path.endswith("requirements.txt"):
            new_content = clean_requirements_text(new_content)

        file_abs.write_text(new_content, encoding="utf-8")
        wrote += 1

    if wrote == 0:
        if _try_json_files_patch(workspace, patch_text):
            return
        if try_apply_git_unified_diff(workspace, raw) > 0:
            return
        if merged_diff.strip() and try_apply_git_unified_diff(workspace, merged_diff) > 0:
            return
        raise ValueError("Patch had no Updatable file blocks and no JSON files[] applied")
