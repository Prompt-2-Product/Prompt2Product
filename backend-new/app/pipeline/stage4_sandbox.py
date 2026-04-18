import os
import subprocess
import asyncio
from pathlib import Path

def detect_run_cmd(output_dir: str, port: int) -> str:
    candidates = [
        ("app/main.py", "uvicorn app.main:app"),
        ("src/main.py", "uvicorn src.main:app"),
        ("giki_coder/main.py", "uvicorn giki_coder.main:app"),
        ("main.py", "uvicorn main:app"),
    ]
    for rel_path, cmd in candidates:
        if os.path.exists(os.path.join(output_dir, rel_path)):
            return f"{cmd} --host 0.0.0.0 --port {port}"
    return f"uvicorn main:app --host 0.0.0.0 --port {port}"

async def run_sandbox_async(output_dir: str, port: int, logger) -> bool:
    """
    Creates a venv, installs deps, and starts uvicorn. 
    Returns True if started successfully.
    """
    output_path = Path(output_dir)
    venv_path = output_path / "venv"
    
    logger("sandbox", "Creating virtual environment...")
    proc = await asyncio.create_subprocess_exec(
        "python3", "-m", "venv", str(venv_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=output_dir
    )
    await proc.communicate()
    
    if proc.returncode != 0:
        logger("fatal", "Failed to create venv.")
        return False
        
    pip_exe = venv_path / "bin" / "pip"
    req_txt = output_path / "requirements.txt"
    
    if req_txt.exists():
        logger("deps", "Installing dependencies...")
        proc = await asyncio.create_subprocess_exec(
            str(pip_exe), "install", "-r", "requirements.txt",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=output_dir
        )
        await proc.communicate()
        if proc.returncode != 0:
            logger("fatal", "Failed to install dependencies.")
            return False

    run_cmd = detect_run_cmd(output_dir, port)
    run_args = run_cmd.split()
    
    uvicorn_exe = venv_path / "bin" / run_args[0]
    
    if not uvicorn_exe.exists():
        logger("fatal", f"Executable {uvicorn_exe} not found in venv.")
        return False

    logger("run", f"Starting application on port {port}...")
    
    # Run uvicorn completely detached
    os.chmod(uvicorn_exe, 0o755)
    
    # We use Popen instead of asyncio.subprocess for fully detached background execution
    try:
        subprocess.Popen(
            [str(uvicorn_exe)] + run_args[1:],
            cwd=output_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        logger("done", f"Application is live tightly on http://localhost:{port}")
        return True
    except Exception as e:
        logger("fatal", f"Failed to start uvicorn: {e}")
        return False
