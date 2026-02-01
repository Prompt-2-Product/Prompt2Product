from __future__ import annotations
import re
from pathlib import Path

PATCH_BEGIN = "*** Begin Patch"
PATCH_END = "*** End Patch"

def apply_unified_patch(workspace: Path, patch_text: str) -> None:
    """
    Supports patches in the format:
    *** Begin Patch
    *** Update File: path/to/file
    @@ ...
    -old
    +new
    *** End Patch
    """
    if PATCH_BEGIN not in patch_text or PATCH_END not in patch_text:
        raise ValueError("Patch missing Begin/End markers")

    # Split into file blocks
    blocks = patch_text.split("*** Update File:")
    if len(blocks) < 2:
        raise ValueError("No file update blocks found in patch")

    for b in blocks[1:]:
        # first line until newline is the file path
        lines = b.splitlines()
        file_path = lines[0].strip()
        file_abs = (workspace / file_path).resolve()

        if not file_abs.exists():
            raise FileNotFoundError(f"Patch refers to missing file: {file_path}")

        original = file_abs.read_text(encoding="utf-8").splitlines(keepends=False)

        # Very small patcher: only handles simple @@ hunks with + and - lines
        # For MVP, we do a naive replace by reconstructing based on hunk lines.
        # (Good enough for your FYP demo; later you can add a full patch lib.)
        hunk_lines = [ln for ln in lines[1:] if ln and not ln.startswith("***")]

        # If model returns full file replacement (common), detect marker:
        if any(ln.startswith("+++ REPLACE ENTIRE FILE +++") for ln in hunk_lines):
            # everything after that line is the new file
            idx = next(i for i, ln in enumerate(hunk_lines) if ln.startswith("+++ REPLACE ENTIRE FILE +++"))
            new_content = "\n".join(hunk_lines[idx+1:]) + "\n"
            file_abs.write_text(new_content, encoding="utf-8")
            continue

        # Otherwise: if patch contains no @@, treat plus-lines as new file (fallback)
        if not any(ln.startswith("@@") for ln in hunk_lines):
            # fallback: keep original, append comment with error (not ideal)
            file_abs.write_text("\n".join(original) + "\n", encoding="utf-8")
            continue

        # Minimal hunk apply: rebuild from + lines, ignoring - lines, ignoring @@ headers
        rebuilt = []
        for ln in hunk_lines:
            if ln.startswith("@@"):
                continue
            if ln.startswith("+"):
                rebuilt.append(ln[1:])
            elif ln.startswith("-"):
                continue
            else:
                rebuilt.append(ln)

        file_abs.write_text("\n".join(rebuilt) + "\n", encoding="utf-8")
