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
        py = str(self._python_path(workspace))
        cmd = [py, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port)]
        return self._exec(cmd, cwd=app_dir)

    def _exec(self, cmd: list[str], cwd: Path) -> ExecResult:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
        return ExecResult(exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)

    def run(self, workspace: Path, entrypoint: str) -> ExecResult:
        py = str(self._python_path(workspace))
        cmd = [py, entrypoint]
        return self._exec(cmd, cwd=workspace)
    
    def run(self, workspace: Path, entrypoint: str) -> ExecResult:
        """
        Generic runner: executes a python file inside the venv.
        Useful for non-uvicorn commands too.
        """
        py = str(self._python_path(workspace))
        cmd = [py, str((workspace / entrypoint).resolve())]
        return self._exec(cmd, cwd=workspace)
