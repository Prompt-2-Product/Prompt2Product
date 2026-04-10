"""
patcher.py — 3-Tier Fallback Patcher for Prompt2Product
========================================================
Tier 1 — Exact Match:        Standard str.replace() after whitespace normalization.
Tier 2 — Fuzzy Match:        Line-by-line similarity scoring to locate the right block
                              even if indentation or trailing spaces differ.
Tier 3 — Full File Rewrite:  If all patch attempts fail, ask the LLM to rewrite the
                              entire file and swap it in atomically.

Every patch attempt is logged. Silent failures are eliminated.
"""

import re
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PatchResult:
    success: bool
    tier_used: str          # "exact", "fuzzy", "full_rewrite", "failed"
    file_path: str
    hunks_applied: int = 0
    hunks_failed: int = 0
    error: str = ""
    original_content: str = ""
    patched_content: str = ""


@dataclass
class Hunk:
    search: str
    replace: str


# ---------------------------------------------------------------------------
# Tier 1 — Exact (whitespace-normalized) match
# ---------------------------------------------------------------------------

def _normalize_whitespace(text: str) -> str:
    """
    Normalize trailing spaces per line and line endings.
    Does NOT change indentation — just strips trailing spaces and normalizes CRLF.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines)


def _try_exact_replace(content: str, hunk: Hunk) -> tuple[bool, str]:
    """
    Attempt 1a: literal replace.
    Attempt 1b: whitespace-normalized replace (retains original indentation in result).
    Returns (success, new_content).
    """
    # 1a: Literal
    if hunk.search in content:
        new_content = content.replace(hunk.search, hunk.replace, 1)
        logger.debug("[Patcher/Exact] Literal match succeeded")
        return True, new_content

    # 1b: Normalize trailing whitespace on both sides, find match, splice in replace
    norm_content = _normalize_whitespace(content)
    norm_search = _normalize_whitespace(hunk.search)

    if norm_search in norm_content:
        new_content = norm_content.replace(norm_search, _normalize_whitespace(hunk.replace), 1)
        logger.debug("[Patcher/Exact] Whitespace-normalized match succeeded")
        return True, new_content

    return False, content


# ---------------------------------------------------------------------------
# Tier 2 — Fuzzy line-by-line match
# ---------------------------------------------------------------------------

def _line_similarity(a: str, b: str) -> float:
    """Ratio of similarity between two stripped lines."""
    return SequenceMatcher(None, a.strip(), b.strip()).ratio()


def _find_fuzzy_block(content_lines: list[str], search_lines: list[str], threshold: float = 0.85) -> int:
    """
    Slide a window of len(search_lines) over content_lines.
    Returns the start index of the best matching window, or -1 if below threshold.
    """
    n = len(search_lines)
    best_score = 0.0
    best_idx = -1

    for i in range(len(content_lines) - n + 1):
        window = content_lines[i : i + n]
        scores = [_line_similarity(w, s) for w, s in zip(window, search_lines)]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        if avg_score > best_score:
            best_score = avg_score
            best_idx = i

    if best_score >= threshold:
        logger.debug(f"[Patcher/Fuzzy] Best match at line {best_idx} with score {best_score:.2f}")
        return best_idx

    logger.warning(f"[Patcher/Fuzzy] Best score {best_score:.2f} below threshold {threshold}")
    return -1


def _try_fuzzy_replace(content: str, hunk: Hunk, threshold: float = 0.85) -> tuple[bool, str]:
    """
    Attempt fuzzy block replacement.
    Preserves the indentation of the matched block in the file
    (uses the actual indentation from the file, not the LLM's guess).
    """
    content_lines = content.split("\n")
    search_lines = hunk.search.strip("\n").split("\n")
    replace_lines = hunk.replace.strip("\n").split("\n")

    idx = _find_fuzzy_block(content_lines, search_lines, threshold)
    if idx == -1:
        return False, content

    # Detect dominant indentation of matched block in the real file
    matched_block = content_lines[idx : idx + len(search_lines)]
    real_indent = ""
    for line in matched_block:
        if line.strip():
            real_indent = line[: len(line) - len(line.lstrip())]
            break

    # Detect dominant indentation of the replace block
    replace_indent = ""
    for line in replace_lines:
        if line.strip():
            replace_indent = line[: len(line) - len(line.lstrip())]
            break

    # Re-indent replace block to match real file indentation
    if replace_indent != real_indent:
        adjusted_replace = []
        for line in replace_lines:
            if line.startswith(replace_indent):
                adjusted_replace.append(real_indent + line[len(replace_indent):])
            else:
                adjusted_replace.append(line)
        replace_lines = adjusted_replace

    new_lines = content_lines[:idx] + replace_lines + content_lines[idx + len(search_lines):]
    logger.info(f"[Patcher/Fuzzy] Applied fuzzy replacement at line {idx}")
    return True, "\n".join(new_lines)


# ---------------------------------------------------------------------------
# Tier 3 — Full file rewrite
# ---------------------------------------------------------------------------

def _apply_full_rewrite(new_content: str) -> tuple[bool, str]:
    """Simply accept the new content as-is. Validation happens upstream."""
    if not new_content or not new_content.strip():
        return False, ""
    logger.info("[Patcher/FullRewrite] Applying full file rewrite")
    return True, new_content


# ---------------------------------------------------------------------------
# Core apply function
# ---------------------------------------------------------------------------

def apply_patch(
    file_path: str | Path,
    hunks: list[Hunk],
    full_rewrite_content: str = "",
    fuzzy_threshold: float = 0.85,
    dry_run: bool = False,
) -> PatchResult:
    """
    Apply a patch to a file using the 3-tier strategy.

    Args:
        file_path:             Path to the target file.
        hunks:                 List of Hunk objects (search/replace pairs).
        full_rewrite_content:  If provided and all hunks fail, use this as final fallback.
        fuzzy_threshold:       Similarity threshold for fuzzy matching (0–1).
        dry_run:               If True, compute result but don't write to disk.

    Returns:
        PatchResult with full diagnostics.
    """
    path = Path(file_path)
    if not path.exists():
        return PatchResult(
            success=False,
            tier_used="failed",
            file_path=str(file_path),
            error=f"File not found: {file_path}",
        )

    original_content = path.read_text(encoding="utf-8")
    current_content = original_content
    hunks_applied = 0
    hunks_failed = 0
    tier_used = "none"

    # ---- If full_rewrite_content is provided and no hunks, go straight to rewrite ----
    if not hunks and full_rewrite_content:
        ok, new_content = _apply_full_rewrite(full_rewrite_content)
        if ok:
            if not dry_run:
                path.write_text(new_content, encoding="utf-8")
            return PatchResult(
                success=True,
                tier_used="full_rewrite",
                file_path=str(file_path),
                hunks_applied=1,
                original_content=original_content,
                patched_content=new_content,
            )
        return PatchResult(
            success=False,
            tier_used="failed",
            file_path=str(file_path),
            error="Full rewrite content was empty",
        )

    # ---- Process each hunk through tiers ----
    for i, hunk in enumerate(hunks):
        applied = False

        # Tier 1: Exact
        ok, new_content = _try_exact_replace(current_content, hunk)
        if ok:
            current_content = new_content
            hunks_applied += 1
            tier_used = "exact"
            applied = True
            logger.info(f"[Patcher] Hunk {i+1}: applied via Tier 1 (exact)")

        # Tier 2: Fuzzy
        if not applied:
            ok, new_content = _try_fuzzy_replace(current_content, hunk, fuzzy_threshold)
            if ok:
                current_content = new_content
                hunks_applied += 1
                tier_used = "fuzzy"
                applied = True
                logger.info(f"[Patcher] Hunk {i+1}: applied via Tier 2 (fuzzy)")

        # Tier 3: Full rewrite (if provided)
        if not applied and full_rewrite_content:
            ok, new_content = _apply_full_rewrite(full_rewrite_content)
            if ok:
                current_content = new_content
                hunks_applied += 1
                tier_used = "full_rewrite"
                applied = True
                logger.info(f"[Patcher] Hunk {i+1}: fell back to Tier 3 (full rewrite)")

        if not applied:
            hunks_failed += 1
            logger.error(
                f"[Patcher] Hunk {i+1}: ALL TIERS FAILED.\n"
                f"  SEARCH was:\n{hunk.search[:200]}\n"
                f"  File excerpt:\n{current_content[:200]}"
            )

    # ---- Write result ----
    overall_success = hunks_applied > 0 and hunks_failed == 0
    partial_success = hunks_applied > 0 and hunks_failed > 0

    if partial_success:
        logger.warning(f"[Patcher] Partial patch: {hunks_applied} applied, {hunks_failed} failed")

    if overall_success or partial_success:
        if not dry_run:
            path.write_text(current_content, encoding="utf-8")

    return PatchResult(
        success=overall_success or partial_success,
        tier_used=tier_used,
        file_path=str(file_path),
        hunks_applied=hunks_applied,
        hunks_failed=hunks_failed,
        error="" if (overall_success or partial_success) else "All hunks failed",
        original_content=original_content,
        patched_content=current_content,
    )


# ---------------------------------------------------------------------------
# Convenience: apply from editor output dict
# ---------------------------------------------------------------------------

def apply_editor_output(
    file_path: str | Path,
    editor_output: dict,
    dry_run: bool = False,
) -> PatchResult:
    """
    Bridge between modifier.parse_editor_response() output and apply_patch().

    editor_output is the dict returned by modifier.parse_editor_response():
      {"mode": "hunk"|"full_rewrite"|"unknown", "hunks": [...], "full_content": "..."}
    """
    mode = editor_output.get("mode", "unknown")

    if mode == "full_rewrite":
        return apply_patch(
            file_path=file_path,
            hunks=[],
            full_rewrite_content=editor_output.get("full_content", ""),
            dry_run=dry_run,
        )

    if mode in ("hunk", "legacy"):
        raw_hunks = editor_output.get("hunks", [])
        hunks = [Hunk(search=h["search"], replace=h["replace"]) for h in raw_hunks]
        full_rewrite_fallback = editor_output.get("full_content", "")
        return apply_patch(
            file_path=file_path,
            hunks=hunks,
            full_rewrite_content=full_rewrite_fallback,
            dry_run=dry_run,
        )

    # Unknown mode — we have nothing usable
    return PatchResult(
        success=False,
        tier_used="failed",
        file_path=str(file_path),
        error=f"Editor returned unknown mode '{mode}'. Raw output: {editor_output.get('raw', '')[:300]}",
    )


# ---------------------------------------------------------------------------
# Rollback support
# ---------------------------------------------------------------------------

def rollback(result: PatchResult) -> bool:
    """Restore a file to its state before the patch was applied."""
    if not result.original_content:
        logger.error("[Patcher/Rollback] No original content stored in PatchResult")
        return False
    path = Path(result.file_path)
    path.write_text(result.original_content, encoding="utf-8")
    logger.info(f"[Patcher/Rollback] Restored {result.file_path}")
    return True
