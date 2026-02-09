from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from app.services.sandbox.base import SandboxRunner, ExecResult

class VenvSandboxRunner(SandboxRunner):
    def __init__(self, venv_dir_name: str = ".venv_sandbox"):
        self.venv_dir_name = venv_dir_name

    def _venv_dir(self, workspace: Path) -> Path:
        return workspace / self.venv_dir_name

    def check_syntax(self, workspace: Path) -> str | None:
        """
        Runs python -m py_compile on all .py files in generated_app/backend.
        Returns error string if any, else None.
        """
        backend_dir = workspace / "generated_app" / "backend"
        if not backend_dir.exists():
            return "Backend directory not found"

        # Find all .py files
        py_files = list(backend_dir.rglob("*.py"))
        if not py_files:
            return None

        for py_file in py_files:
            # Run compile
            # We run inside venv
            cmd = [str(self._python_executable(workspace)), "-m", "py_compile", str(py_file)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                # Syntax error
                return f"SyntaxError in {py_file.name}:\n{res.stderr}"
        
        return None

    def _python_executable(self, workspace: Path) -> Path:
        if sys.platform == "win32":
            return workspace / ".venv_sandbox" / "Scripts" / "python.exe"
        else:
            return workspace / ".venv_sandbox" / "bin" / "python"

    def _python_path(self, workspace: Path) -> Path:
        venv_dir = self._venv_dir(workspace)
        if os.name == "nt":
            return venv_dir / "Scripts" / "python.exe"
        return venv_dir / "bin" / "python"

    def _pip_cmd(self, workspace: Path) -> list[str]:
        return [str(self._python_path(workspace)), "-m", "pip"]

    def setup(self, workspace: Path) -> None:
        venv_dir = self._venv_dir(workspace)
        if not venv_dir.exists():
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            # Pre-install core dependencies as a safety baseline
            cmd = self._pip_cmd(workspace) + ["install", "fastapi", "uvicorn", "aiofiles"]
            subprocess.run(cmd, check=True)

    def install_deps(self, workspace: Path, requirements_path: Path) -> ExecResult:
        if (not requirements_path.exists()) or requirements_path.read_text(encoding="utf-8").strip() == "":
            return ExecResult(exit_code=0, stdout="No requirements to install.", stderr="")

        cmd = self._pip_cmd(workspace) + [
            "install",
            "--no-input",
            "--disable-pip-version-check",
            "--default-timeout", "120",
            "-r", str(requirements_path),
        ]
        return self._exec(cmd, cwd=workspace)

    async def _wait_for_port(self, host: str, port: int, timeout: int = 15) -> bool:
        import socket
        import time
        start = time.time()
        while time.time() - start < timeout:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                try:
                    s.connect((host, port))
                    return True
                except (socket.timeout, ConnectionRefusedError):
                    time.sleep(1)
        return False

    def run_uvicorn(self, workspace: Path, app_dir: Path, host: str, port: int) -> ExecResult:
        import time
        import asyncio
        py = str(self._python_path(workspace))
        cmd = [py, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port)]
        
        # Prepare log files
        log_dir = workspace / ".logs"
        log_dir.mkdir(exist_ok=True)
        
        # Use 'a' append mode to persist logs across attempts
        with open(log_dir / "uvicorn.stdout.log", "a", encoding="utf-8") as out_log, \
             open(log_dir / "uvicorn.stderr.log", "a", encoding="utf-8") as err_log:

            try:
                proc = subprocess.Popen(
                    cmd, 
                    cwd=str(app_dir), 
                    stdout=out_log, 
                    stderr=err_log,
                    text=True
                )
                
                # Check for early exit (e.g. invalid arguments, port already in use)
                time.sleep(2)
                if proc.poll() is not None:
                    # Process exited immediately
                    stdout = (log_dir / "uvicorn.stdout.log").read_text(encoding="utf-8")
                    stderr = (log_dir / "uvicorn.stderr.log").read_text(encoding="utf-8")
                    return ExecResult(exit_code=proc.returncode, stdout=stdout, stderr=stderr or "Process failed to start")

                # Wait for port to become active
                # Since run_uvicorn is sync, we use a simple loop
                is_up = False
                import socket
                start_wait = time.time()
                while time.time() - start_wait < 10:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        try:
                            s.connect((host if host != "0.0.0.0" else "127.0.0.1", port))
                            is_up = True
                            break
                        except (socket.timeout, ConnectionRefusedError):
                            if proc.poll() is not None: break
                            time.sleep(1)

                if is_up:
                    return ExecResult(exit_code=0, stdout=f"Uvicorn started and listening on http://{host}:{port}", stderr="")
                else:
                    # Check if it crashed during wait
                    if proc.poll() is not None:
                        stdout = (log_dir / "uvicorn.stdout.log").read_text(encoding="utf-8")
                        stderr = (log_dir / "uvicorn.stderr.log").read_text(encoding="utf-8")
                        return ExecResult(exit_code=proc.returncode, stdout=stdout, stderr=stderr)
                    return ExecResult(exit_code=1, stdout="Uvicorn started but port timed out", stderr="Health check failed")
                    
            except Exception as e:
                return ExecResult(exit_code=1, stdout="", stderr=str(e))
        # Note: We don't have a 'finally' that closes if it's still running, 
        # because the subprocess owns the duped handles. 
        # But our python file objects should be closed eventually or let GC handle them.
        # However, if we return Success, we don't want to close them if it kills the stream? 
        # Actually it won't on Windows/Linux Popen.


    def _exec(self, cmd: list[str], cwd: Path) -> ExecResult:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
        return ExecResult(exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)

    def run(self, workspace: Path, entrypoint: str) -> ExecResult:
        """
        Generic runner: executes a python file inside the venv.
        Useful for non-uvicorn commands too.
        """
        py = str(self._python_path(workspace))
        cmd = [py, str((workspace / entrypoint).resolve())]
        return self._exec(cmd, cwd=workspace)
