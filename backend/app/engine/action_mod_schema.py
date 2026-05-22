from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.engine.actions.declarative import (
    DeclarativeActionDefinition,
    DeclarativeActionTargetSpec as ActionTargetSpec,
    DeclarativeCheck as ActionCheckSpec,
    DeclarativeCondition as ActionPreconditionSpec,
    DeclarativeOutcome as ActionOutcomeSpec,
)
from app.engine.actions.schemas import SuccessLevel
from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.security import contains_secret_text


class ModActionOutcomeType(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    INVALID = "invalid"


class ModActionDefinition(DeclarativeActionDefinition):
    @property
    def action_id(self) -> str:
        return self.id


class ActionMod(BaseModel):
    manifest: PackageManifestV2
    actions: list[ModActionDefinition] = Field(default_factory=list)

    @field_validator("actions")
    @classmethod
    def _unique_actions(cls, value: list[ModActionDefinition]) -> list[ModActionDefinition]:
        seen: set[str] = set()
        for action in value:
            if action.id in seen:
                raise ValueError(f"duplicate action_id: {action.id}")
            seen.add(action.id)
        return value

    @model_validator(mode="after")
    def _validate_security(self) -> "ActionMod":
        if self.manifest.package_type != PackageTypeV2.ACTION_MOD:
            raise ValueError("action mod manifest must use package_type=action_mod")
        payload = self.model_dump(mode="json")
        if contains_secret_text(str(payload)):
            raise ValueError("action mod contains secret-like text")
        forbidden = {"arbitrary_code", "call_llm"}
        text = str(payload).lower()
        for marker in forbidden:
            if marker in text:
                raise ValueError(f"action mod cannot request {marker}")
        required = {SuccessLevel.SUCCESS, SuccessLevel.FAILURE}
        for action in self.actions:
            missing = required - set(action.outcomes)
            if missing:
                raise ValueError(f"action {action.id} is missing required outcomes")
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            **self.manifest.safe_summary(),
            "action_count": len(self.actions),
            "action_ids": [action.id for action in self.actions],
            "arbitrary_code": False,
            "calls_llm": False,
        }
