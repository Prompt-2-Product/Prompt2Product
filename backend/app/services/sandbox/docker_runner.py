from pathlib import Path
from app.services.sandbox.base import SandboxRunner, ExecResult

class DockerSandboxRunner(SandboxRunner):
    def setup(self, workspace: Path) -> None:
        raise NotImplementedError("Docker runner will be added later")

    def install_deps(self, workspace: Path, requirements_path: Path) -> ExecResult:
        raise NotImplementedError("Docker runner will be added later")

    def run(self, workspace: Path, entrypoint: str) -> ExecResult:
        raise NotImplementedError("Docker runner will be added later")
