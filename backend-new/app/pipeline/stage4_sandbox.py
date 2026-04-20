import os
import sys
import subprocess
import asyncio
from pathlib import Path

# Well-known venv that already has fastapi, jinja2, uvicorn etc installed
FYP_VENV = Path("/home/noor/FYP/venv")
FYP_PIP = FYP_VENV / "bin" / "pip"
FYP_UVICORN = FYP_VENV / "bin" / "uvicorn"


def detect_run_cmd(output_dir: str, port: int) -> tuple[str, list[str]]:
    """Returns (module_string, full_args_list) for the uvicorn app target."""
    candidates = [
        ("app/main.py", "app.main:app"),
        ("src/main.py", "src.main:app"),
        ("giki_coder/main.py", "giki_coder.main:app"),
        ("main.py", "main:app"),
    ]
    for rel_path, module in candidates:
        if os.path.exists(os.path.join(output_dir, rel_path)):
            return module, ["--host", "0.0.0.0", "--port", str(port)]
    return "main:app", ["--host", "0.0.0.0", "--port", str(port)]


async def _run(cmd: list[str], cwd: str) -> int:
    """Run a subprocess, return exit code."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")


async def run_sandbox_async(output_dir: str, port: int, logger) -> object:
    """
    Creates a venv, installs deps (with fallback), and starts uvicorn.
    Falls back to system uvicorn if venv approach fails.
    Returns a Popen handle on success, None on failure.
    """
    output_path = Path(output_dir)
    venv_path = output_path / "venv"
    pip_exe = venv_path / "bin" / "pip"
    venv_uvicorn = venv_path / "bin" / "uvicorn"
    req_txt = output_path / "requirements.txt"

    # ── Step 1: Create virtual environment ──────────────────────────────────
    logger("sandbox", "Creating virtual environment...")
    code, _, err = await _run(["python3", "-m", "venv", str(venv_path)], output_dir)
    if code != 0:
        logger("warn", f"venv creation failed: {err.strip()[:200]}. Will use system Python.", "WARNING")
        venv_created = False
    else:
        venv_created = True

    # ── Step 2: Install dependencies ─────────────────────────────────────────
    if req_txt.exists():
        if venv_created:
            logger("deps", "Installing dependencies...")
            code, _, err = await _run([str(pip_exe), "install", "-r", "requirements.txt"], output_dir)

            if code != 0:
                logger("warn", "Bulk install failed. Trying package-by-package fallback...", "WARNING")
                installed = 0
                failed_pkgs = []

                # Parse packages: handle both one-per-line AND space/comma-separated on one line
                raw_lines = [
                    line.strip()
                    for line in req_txt.read_text().splitlines()
                    if line.strip() and not line.startswith("#")
                ]
                packages = []
                for line in raw_lines:
                    # Split further on spaces and commas (LLM sometimes puts all on one line)
                    parts = [p.strip() for p in line.replace(",", " ").split()]
                    packages.extend([p for p in parts if p])

                for pkg in packages:
                    c, _, _ = await _run([str(pip_exe), "install", pkg], output_dir)
                    if c == 0:
                        installed += 1
                    else:
                        # Try FYP venv pip as secondary fallback for known-good packages
                        if FYP_PIP.exists():
                            c2, _, _ = await _run([str(FYP_PIP), "install", pkg], output_dir)
                            if c2 == 0:
                                installed += 1
                                continue
                        failed_pkgs.append(pkg)

                if failed_pkgs:
                    logger("warn", f"Skipped {len(failed_pkgs)} unresolvable package(s): {', '.join(failed_pkgs[:5])}", "WARNING")
                logger("deps", f"Installed {installed}/{len(packages)} dependencies successfully.")
        else:
            # No venv — try FYP venv pip then system pip
            logger("deps", "No venv available. Trying FYP venv pip...", "WARNING")
            if FYP_PIP.exists():
                code, _, _ = await _run(
                    [str(FYP_PIP), "install", "-r", "requirements.txt"],
                    output_dir
                )
                if code == 0:
                    logger("deps", "Dependencies installed via FYP venv pip.")
                else:
                    logger("warn", "FYP pip install also failed. App may have missing imports.", "WARNING")
            else:
                code, _, _ = await _run(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--break-system-packages"],
                    output_dir
                )
                if code != 0:
                    logger("warn", "System pip install also failed. App may have missing imports.", "WARNING")

    # ── Step 3: Detect target module ─────────────────────────────────────────
    app_module, run_args = detect_run_cmd(output_dir, port)
    logger("run", f"Starting application on port {port}...")

    # ── Step 4: Try to launch with venv uvicorn, fallback to system uvicorn ──
    uvicorn_candidates = []
    if venv_created and venv_uvicorn.exists():
        uvicorn_candidates.append(str(venv_uvicorn))
    # FYP venv has fastapi/jinja2 etc already — best fallback
    if FYP_UVICORN.exists():
        uvicorn_candidates.append(str(FYP_UVICORN))
    # System uvicorn last
    uvicorn_candidates.append("uvicorn")
    uvicorn_candidates.append(f"{sys.executable} -m uvicorn")

    for uvicorn_cmd in uvicorn_candidates:
        try:
            cmd_parts = uvicorn_cmd.split() + [app_module] + run_args
            proc = subprocess.Popen(
                cmd_parts,
                cwd=output_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger("done", f"Application is live on http://localhost:{port}")
            logger("done", f"Forge process complete! Access your app on port {port}")
            return proc
        except FileNotFoundError:
            logger("warn", f"uvicorn not found at '{uvicorn_cmd}', trying next...", "WARNING")
            continue
        except Exception as e:
            logger("fatal", f"Failed to start with '{uvicorn_cmd}': {e}", "ERROR")
            continue

    logger("fatal", "All launch strategies exhausted. No uvicorn available.", "ERROR")
    return None
