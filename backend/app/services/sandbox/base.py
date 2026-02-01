from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str

class SandboxRunner(ABC):
    @abstractmethod
    def setup(self, workspace: Path) -> None: ...

    @abstractmethod
    def install_deps(self, workspace: Path, requirements_path: Path) -> ExecResult: ...

    @abstractmethod
    def run(self, workspace: Path, entrypoint: str) -> ExecResult: ...
