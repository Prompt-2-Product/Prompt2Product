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

    def run_uvicorn(self, workspace: Path, app_dir: Path, host: str, port: int) -> ExecResult:
        import time
        py = str(self._python_path(workspace))
        cmd = [py, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port)]
        
        # Start uvicorn without blocking
        # We want to wait a bit to see if it crashes (syntax error, etc)
        # If it runs for 5 seconds, we assume it's good (for the purpose of generation success),
        # but we must eventually return to the orchestrator to mark 'Success'.
        # Since the Orchestrator loop expects a return, we cannot keep it running indefinitely in this process.
        # We will terminate it after verification.
        
        # Prepare log files
        log_dir = workspace / ".logs"
        log_dir.mkdir(exist_ok=True)
        out_log = open(log_dir / "uvicorn.stdout.log", "w", encoding="utf-8")
        err_log = open(log_dir / "uvicorn.stderr.log", "w", encoding="utf-8")

        try:
            # Start uvicorn without blocking, redirecting output to files
            proc = subprocess.Popen(
                cmd, 
                cwd=str(app_dir), 
                stdout=out_log, 
                stderr=err_log,
                text=True
            )
            
            # Wait for 5 seconds to catch early startup errors
            try:
                ret = proc.wait(timeout=5)
                # If we get here, the process exited within 5 seconds -> Failure (likely)
                
                # Close the handles so we can read them
                out_log.close()
                err_log.close()
                
                stdout = (log_dir / "uvicorn.stdout.log").read_text(encoding="utf-8")
                stderr = (log_dir / "uvicorn.stderr.log").read_text(encoding="utf-8")
                
                return ExecResult(exit_code=ret, stdout=stdout, stderr=stderr or "Process exited early")
            except subprocess.TimeoutExpired:
                # Process is still running after 5 seconds -> Success!
                # Do NOT kill it. Leave it running.
                
                # We should close the handles so they flush, but the subprocess still has them?
                # Actually, better to keep them open if we want logging to continue.
                # But we definitely need to flush? out_log.flush()
                out_log.flush()
                err_log.flush()
                # We don't close them here because uvicorn is still running.
                return ExecResult(exit_code=0, stdout="Uvicorn started successfully (running in background)", stderr="")
                
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
