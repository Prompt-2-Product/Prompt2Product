from __future__ import annotations
from dataclasses import dataclass
from app.core.config import settings

@dataclass(frozen=True)
class ModelChoice:
    model: str

class ModelRouter:
    def spec_model(self) -> ModelChoice:
        return ModelChoice(settings.MODEL_SPEC)

    def code_model(self) -> ModelChoice:
        return ModelChoice(settings.MODEL_CODE)

    def repair_model(self) -> ModelChoice:
        return ModelChoice(settings.MODEL_REPAIR)

    def enhance_model(self) -> ModelChoice:
        return ModelChoice(settings.MODEL_ENHANCE)
