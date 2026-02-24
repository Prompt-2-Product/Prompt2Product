import re
from pathlib import Path
from app.core.utils import clean_requirements_text

PATCH_BEGIN = "*** Begin Patch"
PATCH_END = "*** End Patch"

def apply_unified_patch(workspace: Path, patch_text: str) -> None:
    """
    Supports patches in the format:
    *** Begin Patch
    *** Update File: path/to/file
    +++ REPLACE ENTIRE FILE +++
    new content
    *** End Patch
    """
    patch_text = patch_text.strip()
    
    # Handle markdown code blocks if LLM wraps the patch
    # Robustly remove ``` from start/end
    patch_text = re.sub(r"^```(?:\w+)?\s*", "", patch_text)
    patch_text = re.sub(r"\s*```$", "", patch_text)
    patch_text = patch_text.strip()

    # Lenient check: If we have "Update File:", we can probably proceed even if markers are missing
    if "*** Update File:" not in patch_text:
        if PATCH_BEGIN not in patch_text:
             raise ValueError("Patch missing Begin/End markers and no file updates found")

    # Split into file blocks
    # We use regex to split by '*** Update File:' safely
    blocks = re.split(r"\*\*\* Update File:\s*", patch_text)
    
    # blocks[0] is typically the text before the first '*** Update File:'
    # which should be '*** Begin Patch\n' or similar.
    
    for b in blocks[1:]:
        if not b.strip():
            continue
            
        lines = b.splitlines()
        file_path = lines[0].strip()
        # End of this block might contain '*** End Patch' - strip it from the last line of the block
        content_lines = lines[1:]
        if content_lines and PATCH_END in content_lines[-1]:
            content_lines[-1] = content_lines[-1].replace(PATCH_END, "").strip()
            if not content_lines[-1]:
                content_lines.pop()

        file_abs = (workspace / file_path).resolve()
        if not file_abs.exists():
            # If it doesn't exist, we might be creating it? 
            # But the prompt says "Update File". For FYP, we'll allow creation.
            file_abs.parent.mkdir(parents=True, exist_ok=True)

        # Full file replacement logic
        new_content = ""
        if any(ln.startswith("+++ REPLACE ENTIRE FILE +++") for ln in content_lines):
            idx = next(i for i, ln in enumerate(content_lines) if ln.startswith("+++ REPLACE ENTIRE FILE +++"))
            new_content = "\n".join(content_lines[idx+1:]) + "\n"
        else:
            # Fallback for LLMs that forget the +++ REPLACE ENTIRE FILE +++ marker 
            # but followed everything else: treat as full replacement since it's cleaner.
            # We filter out any remaining markers just in case.
            clean_lines = [ln for ln in content_lines if not ln.startswith("***")]
            new_content = "\n".join(clean_lines) + "\n"

        # AGGRESSIVE CLEANING FOR REQUIREMENTS
        if file_path.endswith("requirements.txt"):
            new_content = clean_requirements_text(new_content)

        file_abs.write_text(new_content, encoding="utf-8")
