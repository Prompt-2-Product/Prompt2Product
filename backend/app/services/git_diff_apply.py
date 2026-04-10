"""
Apply git/unified diffs often produced by LLMs (diff --git / --- / +++ / @@ hunks).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class _Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[tuple[str, str]] = field(default_factory=list)


def _norm_line(s: str) -> str:
    return s.rstrip("\n\r").rstrip()


def _lines_match(file_line: str, diff_line: str) -> bool:
    """Allow minor whitespace drift between disk and LLM-emitted hunks."""
    a, b = _norm_line(file_line), _norm_line(diff_line)
    return a == b or a.strip() == b.strip()


def _safe_workspace_path(workspace: Path, rel: str) -> Path | None:
    rel = rel.replace("\\", "/").strip().lstrip("/")
    if not rel or ".." in rel.split("/"):
        return None
    p = (workspace / rel).resolve()
    ws = workspace.resolve()
    try:
        p.relative_to(ws)
    except ValueError:
        return None
    return p


def _parse_diff_path(line: str) -> str | None:
    # --- a/foo or --- foo\t2024-...
    if not line.startswith("--- ") and not line.startswith("+++ "):
        return None
    raw = line[4:].split("\t", 1)[0].strip()
    if raw == "/dev/null":
        return None
    raw = raw.replace("\\", "/")
    for prefix in ("a/", "b/"):
        if raw.startswith(prefix) and len(raw) > len(prefix):
            raw = raw[len(prefix) :]
            break
    raw = re.sub(r"\.orig$", "", raw, flags=re.I)
    return raw or None


def _parse_hunk_header(line: str) -> _Hunk | None:
    m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
    if not m:
        return None
    o_s, o_c, n_s, n_c = m.groups()
    return _Hunk(
        old_start=int(o_s),
        old_count=int(o_c) if o_c is not None else 1,
        new_start=int(n_s),
        new_count=int(n_c) if n_c is not None else 1,
    )


def _split_into_file_sections(block: str) -> list[str]:
    """Split a patch into one string per file (diff --git sections or first ---/+++ group)."""
    block = block.strip()
    if not block:
        return []
    if re.search(r"(?m)^diff --git ", block):
        parts = re.split(r"(?m)(?=^diff --git )", block)
        return [p.strip() for p in parts if p.strip()]
    return [block]


def _parse_file_section(section: str) -> tuple[str | None, list[_Hunk]] | None:
    lines = section.split("\n")
    target: str | None = None
    i = 0
    while i < len(lines):
        if lines[i].startswith("+++ "):
            target = _parse_diff_path(lines[i])
            break
        i += 1
    if not target:
        return None

    hunks: list[_Hunk] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        h = _parse_hunk_header(ln)
        if h is None:
            i += 1
            continue
        i += 1
        body: list[tuple[str, str]] = []
        while i < len(lines):
            nxt = lines[i]
            if _parse_hunk_header(nxt) or nxt.startswith("diff --git "):
                break
            if nxt.startswith("\\"):
                i += 1
                continue
            if not nxt:
                i += 1
                continue
            prefix = nxt[0]
            if prefix not in " +-":
                i += 1
                continue
            body.append((prefix, nxt[1:]))
            i += 1
        h.lines = body
        hunks.append(h)
    if not hunks:
        return None
    return target, hunks


def _apply_hunks(old_lines: list[str], hunks: list[_Hunk]) -> list[str] | None:
    """Apply hunks in order. old_lines without trailing newline split complexity."""
    old_file = [_norm_line(x) for x in old_lines]
    old_i = 0
    result: list[str] = []

    for h in hunks:
        # Lines in old file before this hunk: hunk.old_start is 1-based index of first old line in hunk
        want_pos = h.old_start - 1
        while old_i < want_pos:
            if old_i >= len(old_file):
                return None
            result.append(old_file[old_i])
            old_i += 1

        for prefix, content in h.lines:
            content = _norm_line(content)
            if prefix == " ":
                if old_i >= len(old_file):
                    return None
                if not _lines_match(old_file[old_i], content):
                    return None
                result.append(old_file[old_i])
                old_i += 1
            elif prefix == "-":
                if old_i >= len(old_file):
                    return None
                if not _lines_match(old_file[old_i], content):
                    return None
                old_i += 1
            elif prefix == "+":
                result.append(content)

    while old_i < len(old_file):
        result.append(old_file[old_i])
        old_i += 1
    return result


def try_apply_git_unified_diff(workspace: Path, text: str) -> int:
    """
    Parse unified / git diff text and write updated files under workspace.
    Returns number of files successfully updated.
    """
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return 0
    if "@@" not in text and "diff --git" not in text:
        if not (text.startswith("---") and "+++" in text):
            return 0

    count = 0
    for section in _split_into_file_sections(text):
        parsed = _parse_file_section(section)
        if not parsed:
            continue
        rel_path, hunks = parsed
        if not rel_path:
            continue
        dest = _safe_workspace_path(workspace, rel_path)
        if dest is None:
            continue

        is_new_file = not dest.exists()
        if is_new_file:
            h0 = hunks[0]
            if h0.old_start != 0 or h0.old_count != 0:
                continue
            old_lines: list[str] = []
        else:
            try:
                raw = dest.read_text(encoding="utf-8")
            except OSError:
                continue
            old_lines = raw.splitlines()

        new_lines = _apply_hunks(old_lines, hunks)
        if new_lines is None:
            continue
        out = "\n".join(new_lines) + "\n"
        if rel_path.endswith("requirements.txt"):
            from app.core.utils import clean_requirements_text

            out = clean_requirements_text(out)
            if not out.endswith("\n"):
                out += "\n"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, encoding="utf-8")
        count += 1
    return count
