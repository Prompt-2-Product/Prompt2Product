"""
execute_modification() — Drop-in replacement for orchestrator.py
================================================================
Paste this method into your Orchestrator class.
Assumes the following are available on self:
  - self.project_dir: Path
  - self.sandbox: VenvSandboxRunner (with .restart() method)
  - self.llm_enhance_feedback(feedback: str) -> str
  - self.llm_call(system: str, user: str) -> str   ← your generic LLM caller

Import at top of orchestrator.py:
  from modifier import (
      build_planner_prompt, parse_planner_response,
      build_editor_prompt, parse_editor_response,
      PLANNER_SYSTEM_PROMPT,
  )
  from patcher import apply_editor_output, rollback, PatchResult
"""

import logging
from pathlib import Path
from modifier import (
    build_planner_prompt,
    parse_planner_response,
    build_editor_prompt,
    parse_editor_response,
    PLANNER_SYSTEM_PROMPT,
)
from patcher import apply_editor_output, rollback

logger = logging.getLogger(__name__)


async def execute_modification(self, raw_feedback: str) -> dict:
    """
    Robust feedback modification pipeline.

    Returns a status dict:
      {
        "success": bool,
        "files_modified": [str],
        "files_failed": [str],
        "tier_used": str,
        "error": str
      }
    """
    results = {
        "success": False,
        "files_modified": [],
        "files_failed": [],
        "tier_used": "",
        "error": "",
    }

    # -----------------------------------------------------------------------
    # Phase 0 — Enhance feedback
    # -----------------------------------------------------------------------
    try:
        enhanced = await self.llm_enhance_feedback(raw_feedback)
        logger.info(f"[Modification] Enhanced feedback: {enhanced[:120]}")
    except Exception as e:
        logger.warning(f"[Modification] Feedback enhancement failed, using raw: {e}")
        enhanced = raw_feedback

    # -----------------------------------------------------------------------
    # Phase 1 — Planner
    # -----------------------------------------------------------------------
    file_tree = self._build_file_tree()  # your existing method
    planner_user = build_planner_prompt(enhanced, file_tree)

    try:
        planner_raw = await self.llm_call(PLANNER_SYSTEM_PROMPT, planner_user)
        files_to_modify, reason = parse_planner_response(planner_raw)
    except Exception as e:
        results["error"] = f"Planner LLM call failed: {e}"
        return results

    if not files_to_modify:
        results["error"] = "Planner returned no files to modify"
        return results

    logger.info(f"[Modification] Plan: modify {files_to_modify} — {reason}")

    # -----------------------------------------------------------------------
    # Phase 2 + 3 — Editor + Patcher (per file)
    # -----------------------------------------------------------------------
    patch_results = []

    for rel_path in files_to_modify:
        abs_path = self.project_dir / rel_path

        if not abs_path.exists():
            logger.error(f"[Modification] Planned file not found: {abs_path}")
            results["files_failed"].append(rel_path)
            continue

        file_content = abs_path.read_text(encoding="utf-8")
        filename = abs_path.name

        # --- Try HUNK mode first (cheaper, more precise) ---
        system_hunk, user_hunk = build_editor_prompt(
            instruction=enhanced,
            filename=filename,
            file_content=file_content,
            mode="hunk",
        )

        editor_raw = await self.llm_call(system_hunk, user_hunk)
        editor_output = parse_editor_response(editor_raw)

        if editor_output["mode"] == "unknown":
            # --- Escalate to FULL REWRITE mode ---
            logger.warning(f"[Modification] Hunk parse failed for {rel_path}, escalating to full rewrite")
            system_rw, user_rw = build_editor_prompt(
                instruction=enhanced,
                filename=filename,
                file_content=file_content,
                mode="full_rewrite",
            )
            editor_raw = await self.llm_call(system_rw, user_rw)
            editor_output = parse_editor_response(editor_raw)

        # --- Apply patch ---
        patch_result = apply_editor_output(abs_path, editor_output)
        patch_results.append((rel_path, patch_result))

        if patch_result.success:
            logger.info(
                f"[Modification] ✓ {rel_path} patched via {patch_result.tier_used} "
                f"({patch_result.hunks_applied} hunk(s))"
            )
            results["files_modified"].append(rel_path)
            results["tier_used"] = patch_result.tier_used
        else:
            logger.error(f"[Modification] ✗ {rel_path} patch failed: {patch_result.error}")
            results["files_failed"].append(rel_path)

    # -----------------------------------------------------------------------
    # Phase 4 — Restart sandbox, verify, rollback on crash
    # -----------------------------------------------------------------------
    if results["files_modified"]:
        try:
            restart_ok = await self.sandbox.restart()
            if not restart_ok:
                # Rollback all successfully patched files
                logger.error("[Modification] Sandbox restart failed — rolling back all patches")
                for rel_path, patch_result in patch_results:
                    if patch_result.success:
                        rollback(patch_result)
                        results["files_modified"].remove(rel_path)
                        results["files_failed"].append(rel_path)
                results["error"] = "Sandbox crashed after patch — changes rolled back"
                return results
        except Exception as e:
            results["error"] = f"Sandbox restart exception: {e}"
            return results

    results["success"] = bool(results["files_modified"])
    return results
