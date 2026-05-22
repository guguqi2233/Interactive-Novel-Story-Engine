from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from app.platform.narrative_project import validate_project_relative_path
from app.platform.rp_mature import CrossModeRPSafetyMetadata, MatureExportFilter, MatureExportPolicy
from app.platform.security import contains_secret_text, redact_text, safe_identifier, validate_relative_package_path
from app.platform.shared_libraries import CrossModeLink, CrossModeLinkRegistry


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class CrossModeArtifactStatus(StrEnum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    VALIDATION_FAILED = "validation_failed"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ARCHIVED = "archived"


class CrossModeDirection(StrEnum):
    NOVEL_TO_WORLD = "novel_to_world"
    WORLD_TO_NOVEL = "world_to_novel"
    TAVERN_TO_WORLD = "tavern_to_world"
    WORLD_TO_TAVERN = "world_to_tavern"
    TAVERN_TO_NOVEL = "tavern_to_novel"
    NOVEL_TO_TAVERN = "novel_to_tavern"


class CrossModeAuditActor(StrEnum):
    USER = "user"
    SYSTEM = "system"
    CODEX = "codex"
    TEST = "test"


class CrossModeAuditResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    REJECTED = "rejected"
    DRY_RUN = "dry_run"


class CrossModeBaseModel(BaseModel):
    model_config = {"use_enum_values": True}

    @model_validator(mode="after")
    def reject_secrets(self) -> "CrossModeBaseModel":
        payload = json.dumps(self.model_dump(mode="json"), ensure_ascii=False)
        if contains_secret_text(payload):
            raise ValueError("Cross-mode artifact must not contain provider secrets or API keys")
        return self


class CrossModeArtifactBase(CrossModeBaseModel):
    artifact_id: str
    project_id: str = "local_project"
    direction: CrossModeDirection
    source_refs: list[str] = Field(default_factory=list)
    target_refs: list[str] = Field(default_factory=list)
    artifact_type: str = "draft"
    status: CrossModeArtifactStatus = CrossModeArtifactStatus.DRAFT
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    hidden: bool = False
    debug_only: bool = False

    def safe_summary(self) -> dict[str, Any] | None:
        if self.hidden or self.debug_only:
            return None
        return {
            "artifact_id": self.artifact_id,
            "project_id": self.project_id,
            "direction": str(self.direction),
            "source_refs": list(self.source_refs),
            "target_refs": list(self.target_refs),
            "artifact_type": self.artifact_type,
            "status": str(self.status),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class CrossModeDraft(CrossModeArtifactBase):
    proposed_content: dict[str, Any] = Field(default_factory=dict)
    validation_status: Literal["draft", "valid", "warning", "invalid", "unvalidated"] = "unvalidated"
    warnings: list[str] = Field(default_factory=list)
    proposed_cross_mode_links: list[CrossModeLink] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any] | None:
        payload = super().safe_summary()
        if payload is None:
            return None
        payload.update(
            {
                "validation_status": self.validation_status,
                "warnings": [redact_text(item) for item in self.warnings],
                "proposed_content": _redact_obj(self.proposed_content),
                "proposed_cross_mode_links": [item.safe_summary() for item in self.proposed_cross_mode_links if item.safe_summary() is not None],
            }
        )
        return payload


class CrossModeProposal(CrossModeBaseModel):
    proposal_id: str
    project_id: str = "local_project"
    draft_id: str
    direction: CrossModeDirection = CrossModeDirection.NOVEL_TO_WORLD
    target_refs: list[str] = Field(default_factory=list)
    proposed_state_deltas: list[dict[str, Any]] = Field(default_factory=list)
    proposed_content_pack_changes: list[dict[str, Any]] = Field(default_factory=list)
    proposed_cross_mode_links: list[CrossModeLink] = Field(default_factory=list)
    review_status: CrossModeArtifactStatus = CrossModeArtifactStatus.PROPOSED
    validation_status: Literal["draft", "valid", "warning", "invalid", "unvalidated"] = "unvalidated"
    safety_notes: list[str] = Field(default_factory=list)
    rp_safety_metadata: CrossModeRPSafetyMetadata | None = None
    hidden: bool = False
    debug_only: bool = False
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    def safe_summary(self) -> dict[str, Any] | None:
        if self.hidden or self.debug_only:
            return None
        return {
            "proposal_id": self.proposal_id,
            "project_id": self.project_id,
            "draft_id": self.draft_id,
            "direction": str(self.direction),
            "target_refs": list(self.target_refs),
            "review_status": str(self.review_status),
            "validation_status": self.validation_status,
            "safety_notes": [redact_text(item) for item in self.safety_notes],
            "rp_safety_metadata": self.rp_safety_metadata.safe_summary() if self.rp_safety_metadata else None,
            "proposed_cross_mode_links": [item.safe_summary() for item in self.proposed_cross_mode_links if item.safe_summary() is not None],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class CrossModeReview(CrossModeBaseModel):
    review_id: str
    project_id: str = "local_project"
    artifact_id: str
    reviewer: str = "user"
    status: Literal["pending", "reviewed", "approved", "rejected"] = "pending"
    notes: str = ""
    created_at: str = Field(default_factory=now_iso)

    def safe_summary(self) -> dict[str, Any]:
        return {**self.model_dump(mode="json"), "notes": redact_text(self.notes)}


class CrossModeApplyPlan(CrossModeBaseModel):
    apply_plan_id: str
    project_id: str = "local_project"
    proposal_id: str
    apply_target: Literal["project", "content_pack", "world_save", "tavern_session", "novel_manuscript"] = "project"
    requires_confirmation: bool = True
    dry_run_result: dict[str, Any] = Field(default_factory=dict)
    expected_changes: list[str] = Field(default_factory=list)
    rollback_notes: str = ""
    validation_status: Literal["draft", "valid", "warning", "invalid", "unvalidated"] = "unvalidated"
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "apply_plan_id": self.apply_plan_id,
            "project_id": self.project_id,
            "proposal_id": self.proposal_id,
            "apply_target": self.apply_target,
            "requires_confirmation": self.requires_confirmation,
            "dry_run_result": _redact_obj(self.dry_run_result),
            "expected_changes": [redact_text(item) for item in self.expected_changes],
            "rollback_notes": redact_text(self.rollback_notes),
            "validation_status": self.validation_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class CrossModeAuditRecord(CrossModeBaseModel):
    audit_id: str
    project_id: str
    action_type: str
    actor: CrossModeAuditActor = CrossModeAuditActor.USER
    source_artifact_id: str | None = None
    target_refs: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=now_iso)
    safe_summary: str = ""
    debug_details_ref: str | None = None
    result: CrossModeAuditResult = CrossModeAuditResult.SUCCESS
    related_event_id: str | None = None

    def normal_summary(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "project_id": self.project_id,
            "action_type": self.action_type,
            "actor": str(self.actor),
            "source_artifact_id": self.source_artifact_id,
            "target_refs": list(self.target_refs),
            "timestamp": self.timestamp,
            "safe_summary": redact_text(self.safe_summary),
            "debug_details_ref": self.debug_details_ref,
            "result": str(self.result),
            "related_event_id": self.related_event_id,
        }


class CrossModeRepository:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.cross_mode_root = (self.project_root / "cross_mode").resolve()
        if self.project_root not in self.cross_mode_root.parents:
            raise ValueError("Cross-mode root escaped project root")
        for section in ("drafts", "proposals", "reviews", "apply_plans", "audit", "timeline_cache", "conflicts"):
            self._dir(section).mkdir(parents=True, exist_ok=True)

    def create_draft(self, draft: CrossModeDraft, *, audit: bool = True) -> CrossModeDraft:
        saved = self.save_draft(draft)
        if audit:
            self.append_audit_record(_audit(saved.project_id, "create_draft", saved.artifact_id, [*saved.source_refs, *saved.target_refs]))
        return saved

    def load_draft(self, draft_id: str) -> CrossModeDraft:
        return CrossModeDraft.model_validate(self._read_yaml("drafts", draft_id))

    def save_draft(self, draft: CrossModeDraft) -> CrossModeDraft:
        updated = draft.model_copy(update={"updated_at": now_iso()})
        self._write_yaml("drafts", updated.artifact_id, updated)
        return updated

    def list_drafts(self) -> list[CrossModeDraft]:
        return sorted([CrossModeDraft.model_validate(item) for item in self._read_all("drafts")], key=lambda item: (item.updated_at, item.artifact_id))

    def create_proposal(self, proposal: CrossModeProposal, *, audit: bool = True) -> CrossModeProposal:
        saved = self.save_proposal(proposal)
        if audit:
            self.append_audit_record(_audit(saved.project_id, "create_proposal", saved.proposal_id, saved.target_refs))
        return saved

    def load_proposal(self, proposal_id: str) -> CrossModeProposal:
        return CrossModeProposal.model_validate(self._read_yaml("proposals", proposal_id))

    def save_proposal(self, proposal: CrossModeProposal) -> CrossModeProposal:
        updated = proposal.model_copy(update={"updated_at": now_iso()})
        self._write_yaml("proposals", updated.proposal_id, updated)
        return updated

    def list_proposals(self) -> list[CrossModeProposal]:
        return sorted([CrossModeProposal.model_validate(item) for item in self._read_all("proposals")], key=lambda item: (item.updated_at, item.proposal_id))

    def create_review(self, review: CrossModeReview) -> CrossModeReview:
        self._write_yaml("reviews", review.review_id, review)
        self.append_audit_record(_audit(review.project_id, "review_proposal", review.artifact_id, []))
        return review

    def save_apply_plan(self, plan: CrossModeApplyPlan) -> CrossModeApplyPlan:
        updated = plan.model_copy(update={"updated_at": now_iso()})
        self._write_yaml("apply_plans", updated.apply_plan_id, updated)
        return updated

    def load_apply_plan(self, apply_plan_id: str) -> CrossModeApplyPlan:
        return CrossModeApplyPlan.model_validate(self._read_yaml("apply_plans", apply_plan_id))

    def list_apply_plans(self) -> list[CrossModeApplyPlan]:
        return sorted([CrossModeApplyPlan.model_validate(item) for item in self._read_all("apply_plans")], key=lambda item: (item.updated_at, item.apply_plan_id))

    def append_audit_record(self, record: CrossModeAuditRecord) -> CrossModeAuditRecord:
        self._write_yaml("audit", record.audit_id, record)
        return record

    def load_audit_record(self, audit_id: str) -> CrossModeAuditRecord:
        return CrossModeAuditRecord.model_validate(self._read_yaml("audit", audit_id))

    def list_audit_records(self) -> list[CrossModeAuditRecord]:
        return sorted([CrossModeAuditRecord.model_validate(item) for item in self._read_all("audit")], key=lambda item: item.timestamp)

    def _dir(self, section: str) -> Path:
        safe = validate_project_relative_path(f"cross_mode/{section}")
        target = (self.project_root / safe).resolve()
        if self.project_root not in target.parents:
            raise ValueError("Cross-mode repository path escaped project root")
        return target

    def _path(self, section: str, item_id: str) -> Path:
        if not safe_identifier(item_id):
            raise ValueError(f"Unsafe cross-mode id: {item_id}")
        return self._dir(section) / f"{item_id}.yaml"

    def _write_yaml(self, section: str, item_id: str, model: BaseModel) -> None:
        path = self._path(section, item_id)
        payload = model.model_dump(mode="json")
        text = json.dumps(payload, ensure_ascii=False)
        if contains_secret_text(text):
            raise ValueError("Refusing to store cross-mode artifact containing secrets")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=True, allow_unicode=True), encoding="utf-8")

    def _read_yaml(self, section: str, item_id: str) -> dict[str, Any]:
        path = self._path(section, item_id)
        if not path.exists():
            raise FileNotFoundError(item_id)
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _read_all(self, section: str) -> list[dict[str, Any]]:
        directory = self._dir(section)
        if not directory.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in sorted(directory.glob("*.yaml")):
            validate_relative_package_path(path.relative_to(self.project_root).as_posix())
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            items.append(data)
        return items


class CrossModeValidationIssue(BaseModel):
    severity: Literal["suggestion", "warning", "error", "blocker"]
    code: str
    message: str
    artifact_ref: str = ""
    safe_details: dict[str, str] = Field(default_factory=dict)
    debug_details: dict[str, str] = Field(default_factory=dict)

    def normal_copy(self) -> "CrossModeValidationIssue":
        return self.model_copy(update={"message": redact_text(self.message), "debug_details": {}, "safe_details": {k: redact_text(v) for k, v in self.safe_details.items()}})


class CrossModeValidationReport(BaseModel):
    project_id: str | None = None
    ok: bool = True
    profile: Literal["normal", "debug"] = "normal"
    blockers: list[CrossModeValidationIssue] = Field(default_factory=list)
    errors: list[CrossModeValidationIssue] = Field(default_factory=list)
    warnings: list[CrossModeValidationIssue] = Field(default_factory=list)
    suggestions: list[CrossModeValidationIssue] = Field(default_factory=list)
    summary: dict[str, int | str | None] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)

    def add(self, issue: CrossModeValidationIssue) -> None:
        if issue.severity == "blocker":
            self.blockers.append(issue)
        elif issue.severity == "error":
            self.errors.append(issue)
        elif issue.severity == "warning":
            self.warnings.append(issue)
        else:
            self.suggestions.append(issue)

    def finalize(self) -> "CrossModeValidationReport":
        self.ok = not self.blockers and not self.errors
        self.summary = {
            "blockers": len(self.blockers),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "suggestions": len(self.suggestions),
            "profile": self.profile,
        }
        return self.normal_copy() if self.profile == "normal" else self

    def normal_copy(self) -> "CrossModeValidationReport":
        return self.model_copy(
            update={
                "profile": "normal",
                "blockers": [item.normal_copy() for item in self.blockers],
                "errors": [item.normal_copy() for item in self.errors],
                "warnings": [item.normal_copy() for item in self.warnings],
                "suggestions": [item.normal_copy() for item in self.suggestions],
            }
        )


class CrossModeValidationService:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.repository = CrossModeRepository(self.project_root)

    def validate(self, *, profile: Literal["normal", "debug"] = "normal") -> CrossModeValidationReport:
        project_id = self._project_id()
        report = CrossModeValidationReport(project_id=project_id, profile=profile)
        known_refs = self._known_refs()
        self._validate_links(report, known_refs)
        self._validate_drafts(report, known_refs)
        self._validate_proposals(report, known_refs)
        self._validate_apply_plans(report)
        self._validate_conflicts(report)
        return report.finalize()

    def _project_id(self) -> str | None:
        manifest = self.project_root / "project.yaml"
        if manifest.exists():
            data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            return data.get("project_id")
        return None

    def _known_refs(self) -> set[str]:
        refs: set[str] = set()
        for folder, prefix, key in (
            ("novel/chapters", "novel:chapter", "chapter_id"),
            ("novel/scenes", "novel:scene", "scene_id"),
            ("novel/manuscripts", "novel:manuscript", "manuscript_id"),
            ("tavern/characters", "tavern:character", "tavern_character_id"),
            ("tavern/sessions", "tavern:session", "session_id"),
            ("tavern/proposals", "tavern:proposal", "proposal_id"),
            ("cross_mode/drafts", "cross_mode:draft", "artifact_id"),
            ("cross_mode/proposals", "cross_mode:proposal", "proposal_id"),
        ):
            directory = self.project_root / folder
            if not directory.exists():
                continue
            for path in directory.glob("*.yaml"):
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                value = data.get(key) or path.stem
                refs.add(f"{prefix}:{value}")
                refs.add(f"{key.split('_')[0]}:{value}")
                refs.add(str(value))
        return refs

    def _validate_links(self, report: CrossModeValidationReport, known_refs: set[str]) -> None:
        for path in sorted(self.project_root.rglob("cross_mode_links.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                items = raw.get("links", raw) if isinstance(raw, dict) else raw
            except Exception as exc:
                report.add(_issue("error", "cross_mode_links_invalid", f"Invalid CrossModeLink registry: {exc}", str(path)))
                continue
            if not isinstance(items, list):
                report.add(_issue("error", "cross_mode_links_invalid_shape", "CrossModeLink registry must be a list", str(path)))
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    report.add(_issue("error", "cross_mode_link_invalid", "CrossModeLink entry must be an object", f"{path}#{index}"))
                    continue
                if item.get("status") == "broken":
                    report.add(_issue("blocker", "cross_mode_link_broken", "CrossModeLink is marked broken", f"{path}#{index}"))
                if item.get("hidden") and item.get("status") != "deprecated":
                    report.add(_issue("error", "cross_mode_hidden_target_risk", "Hidden CrossModeLink cannot appear in normal review", f"{path}#{index}"))
                for field in ("source_ref", "target_ref"):
                    ref = str(item.get(field) or "")
                    if ref and ref not in known_refs and not ref.startswith(("world:", "npc:", "fact:", "quest:", "location:", "relationship:", "timeline:")):
                        report.add(_issue("error", f"cross_mode_link_{field}_missing", f"CrossModeLink {field} does not resolve", f"{path}#{index}", ref=ref))

    def _validate_drafts(self, report: CrossModeValidationReport, known_refs: set[str]) -> None:
        for draft in self.repository.list_drafts():
            payload = json.dumps(draft.safe_summary() or {}, ensure_ascii=False).lower()
            if "gamestate" in payload or "apply_delta" in payload:
                report.add(_issue("blocker", "draft_direct_state_mutation", "Draft appears to request direct GameState mutation", draft.artifact_id))
            if draft.hidden and draft.safe_summary() is not None:
                report.add(_issue("error", "draft_hidden_leak", "Hidden draft leaked into normal summary", draft.artifact_id))
            for ref in draft.source_refs:
                if ref not in known_refs and not ref.startswith(("world:", "npc:", "fact:", "quest:", "location:", "relationship:", "timeline:")):
                    report.add(_issue("error", "draft_source_missing", "CrossModeDraft source_ref does not resolve", draft.artifact_id, ref=ref))

    def _validate_proposals(self, report: CrossModeValidationReport, known_refs: set[str]) -> None:
        for proposal in self.repository.list_proposals():
            if proposal.validation_status in {"draft", "unvalidated"}:
                report.add(_issue("warning", "proposal_unvalidated", "CrossModeProposal has not been validated", proposal.proposal_id))
            payload = json.dumps(proposal.safe_summary() or {}, ensure_ascii=False).lower()
            if "state_delta" in payload or contains_secret_text(payload):
                report.add(_issue("blocker", "proposal_forbidden_material", "Proposal normal summary contains forbidden material", proposal.proposal_id))
            if proposal.direction == CrossModeDirection.TAVERN_TO_WORLD and proposal.rp_safety_metadata is None:
                report.add(_issue("error", "tavern_world_missing_rp_safety_metadata", "Tavern to World proposal is missing RP safety metadata", proposal.proposal_id))
            if proposal.rp_safety_metadata and (proposal.rp_safety_metadata.contains_mature_content or proposal.rp_safety_metadata.contains_mature_memory):
                report.add(_issue("blocker", "cross_mode_mature_content_to_world_blocked", "Mature RP content cannot become World facts", proposal.proposal_id))
            for ref in proposal.target_refs:
                if ref not in known_refs and not ref.startswith(("world:", "npc:", "fact:", "quest:", "location:", "relationship:", "timeline:")):
                    report.add(_issue("error", "proposal_target_missing", "CrossModeProposal target_ref does not resolve", proposal.proposal_id, ref=ref))

    def _validate_apply_plans(self, report: CrossModeValidationReport) -> None:
        for plan in self.repository.list_apply_plans():
            if not plan.requires_confirmation:
                report.add(_issue("blocker", "apply_plan_missing_confirmation", "CrossModeApplyPlan must require explicit confirmation", plan.apply_plan_id))
            if plan.apply_target in {"world_save", "content_pack"} and plan.validation_status in {"draft", "unvalidated"}:
                report.add(_issue("error", "world_apply_plan_unvalidated", "World apply plan must be validated before apply", plan.apply_plan_id))

    def _validate_conflicts(self, report: CrossModeValidationReport) -> None:
        conflict_dir = self.project_root / "cross_mode" / "conflicts"
        if not conflict_dir.exists():
            return
        for path in conflict_dir.glob("*.yaml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            issues = data.get("conflicts") if isinstance(data, dict) else None
            for item in issues or []:
                if item.get("severity") == "blocker":
                    report.add(_issue("blocker", "cross_mode_conflict_blocker", "Cross-mode conflict report contains blocker", path.stem))


class CrossModeTimelineEntry(BaseModel):
    entry_id: str
    source_mode: Literal["novel", "tavern", "world", "authoring", "cross_mode"]
    source_ref: str
    title: str
    safe_summary: str = ""
    chronological_index: int | None = None
    in_world_time: str | None = None
    visibility: Literal["normal", "authoring_only", "hidden", "debug_only"] = "normal"
    linked_cross_mode_links: list[str] = Field(default_factory=list)
    proposal_status: str | None = None


class CrossModeTimelineView(BaseModel):
    project_id: str
    entries: list[CrossModeTimelineEntry] = Field(default_factory=list)


class CrossModeTimelineService:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def build_project_timeline(self, *, include_debug: bool = False) -> CrossModeTimelineView:
        project_id = CrossModeValidationService(self.project_root)._project_id() or "local_project"
        entries: list[CrossModeTimelineEntry] = []
        self._add_yaml_entries(entries, "novel/scenes", "novel", "scene_id", "title", "summary")
        self._add_yaml_entries(entries, "tavern/sessions", "tavern", "session_id", "title", "title")
        self._add_yaml_entries(entries, "cross_mode/drafts", "cross_mode", "artifact_id", "artifact_type", "validation_status")
        self._add_yaml_entries(entries, "cross_mode/proposals", "cross_mode", "proposal_id", "proposal_id", "validation_status")
        filtered = [entry for entry in entries if include_debug or entry.visibility not in {"hidden", "debug_only", "authoring_only"}]
        return CrossModeTimelineView(project_id=project_id, entries=sorted(filtered, key=lambda item: (item.chronological_index is None, item.chronological_index or 0, item.entry_id)))

    def _add_yaml_entries(self, entries: list[CrossModeTimelineEntry], rel: str, mode: str, id_key: str, title_key: str, summary_key: str) -> None:
        directory = self.project_root / rel
        if not directory.exists():
            return
        for index, path in enumerate(sorted(directory.glob("*.yaml"))):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            visibility = str(data.get("visibility", "normal"))
            entries.append(
                CrossModeTimelineEntry(
                    entry_id=f"{mode}_{data.get(id_key, path.stem)}",
                    source_mode=mode,  # type: ignore[arg-type]
                    source_ref=f"{mode}:{id_key.replace('_id', '')}:{data.get(id_key, path.stem)}",
                    title=str(data.get(title_key) or data.get(id_key) or path.stem),
                    safe_summary=redact_text(str(data.get(summary_key) or ""))[:300],
                    chronological_index=data.get("chronological_index", index),
                    visibility=visibility if visibility in {"normal", "authoring_only", "hidden", "debug_only"} else "normal",  # type: ignore[arg-type]
                    proposal_status=str(data.get("validation_status")) if mode == "cross_mode" else None,
                )
            )


class CrossModeLinkReviewReport(BaseModel):
    project_id: str
    ok: bool = True
    broken_links: list[str] = Field(default_factory=list)
    hidden_target_risks: list[str] = Field(default_factory=list)
    duplicate_links: list[str] = Field(default_factory=list)
    stale_links: list[str] = Field(default_factory=list)
    links: list[dict[str, Any]] = Field(default_factory=list)


class CrossModeLinkReviewService:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def review(self) -> CrossModeLinkReviewReport:
        project_id = CrossModeValidationService(self.project_root)._project_id() or "local_project"
        report = CrossModeLinkReviewReport(project_id=project_id)
        seen: set[tuple[str, str, str]] = set()
        for path in sorted(self.project_root.rglob("cross_mode_links.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            items = raw.get("links", raw) if isinstance(raw, dict) else raw
            for item in items or []:
                link = CrossModeLink.model_validate(item)
                summary = link.safe_summary()
                if summary:
                    report.links.append(summary)
                key = (link.source_ref, link.target_ref, link.link_type)
                if key in seen:
                    report.duplicate_links.append(link.link_id)
                seen.add(key)
                if link.status == "broken":
                    report.broken_links.append(link.link_id)
                if link.hidden:
                    report.hidden_target_risks.append(link.link_id)
                if link.status == "deprecated":
                    report.stale_links.append(link.link_id)
        report.ok = not report.broken_links and not report.hidden_target_risks
        return report


class CrossModeConflict(BaseModel):
    conflict_id: str
    conflict_type: str
    severity: Literal["info", "warning", "error", "blocker"] = "warning"
    affected_refs: list[str] = Field(default_factory=list)
    safe_summary: str = ""
    status: Literal["open", "reviewed", "ignored"] = "open"
    debug_only: bool = False


class CrossModeConflictReport(BaseModel):
    project_id: str
    conflicts: list[CrossModeConflict] = Field(default_factory=list)
    ok: bool = True

    def normal_summary(self) -> dict[str, Any]:
        visible = [item for item in self.conflicts if not item.debug_only]
        return {"project_id": self.project_id, "ok": not any(item.severity in {"error", "blocker"} for item in visible), "conflicts": [item.model_dump(mode="json", exclude={"debug_only"}) for item in visible]}


class CrossModeConflictDetector:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def detect(self) -> CrossModeConflictReport:
        project_id = CrossModeValidationService(self.project_root)._project_id() or "local_project"
        report = CrossModeConflictReport(project_id=project_id)
        link_report = CrossModeLinkReviewService(self.project_root).review()
        for link_id in link_report.duplicate_links:
            report.conflicts.append(CrossModeConflict(conflict_id=f"duplicate_{link_id}", conflict_type="duplicate_cross_mode_target", severity="warning", affected_refs=[link_id], safe_summary="Duplicate CrossModeLink target."))
        for link_id in link_report.stale_links:
            report.conflicts.append(CrossModeConflict(conflict_id=f"stale_{link_id}", conflict_type="stale_cross_mode_link", severity="warning", affected_refs=[link_id], safe_summary="Deprecated or stale CrossModeLink."))
        for link_id in link_report.hidden_target_risks:
            report.conflicts.append(CrossModeConflict(conflict_id=f"hidden_{link_id}", conflict_type="fact_visibility_conflict", severity="error", affected_refs=[link_id], safe_summary="Hidden target risk in normal cross-mode view."))
        report.ok = not any(item.severity in {"error", "blocker"} for item in report.conflicts)
        self._save_latest(report)
        return report

    def _save_latest(self, report: CrossModeConflictReport) -> None:
        target = self.project_root / "cross_mode" / "conflicts" / "latest.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump(report.model_dump(mode="json"), sort_keys=True, allow_unicode=True), encoding="utf-8")


class NovelToWorldPipeline:
    def __init__(self, repository: CrossModeRepository) -> None:
        self.repository = repository

    def create_draft(self, *, project_id: str, source_ref: str, draft_type: str, proposed_content: dict[str, Any] | None = None, dry_run: bool = False) -> CrossModeDraft:
        draft = CrossModeDraft(
            artifact_id=f"nw_{_safe_ref_id(source_ref)}_{draft_type}",
            project_id=project_id,
            direction=CrossModeDirection.NOVEL_TO_WORLD,
            source_refs=[source_ref],
            target_refs=[f"world:{draft_type}:{_safe_ref_id(source_ref)}"],
            artifact_type=draft_type,
            proposed_content=_redact_obj(proposed_content or {"source_ref": source_ref, "draft_type": draft_type}),
            validation_status="warning",
            warnings=["Requires World content validation before apply."],
        )
        return draft if dry_run else self.repository.create_draft(draft)

    def validate(self, draft: CrossModeDraft) -> CrossModeDraft:
        payload = json.dumps(draft.proposed_content, ensure_ascii=False).lower()
        status = "invalid" if "hidden" in payload or "state_delta" in payload else "warning"
        warnings = list(draft.warnings)
        if status == "invalid":
            warnings.append("Draft contains hidden or StateDelta-like material.")
        return self.repository.save_draft(draft.model_copy(update={"validation_status": status, "warnings": warnings}))


class WorldToNovelPreview(BaseModel):
    draft_id: str
    source_event_ids: list[str] = Field(default_factory=list)
    safe_event_summaries: list[str] = Field(default_factory=list)
    suggested_chapter_title: str = "World Events"
    draft_summary: str = ""
    draft_text: str | None = None
    hidden_events_excluded_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class WorldToNovelPipeline:
    def __init__(self, repository: CrossModeRepository) -> None:
        self.repository = repository

    def preview(self, *, project_id: str, safe_event_summaries: list[str], source_event_ids: list[str] | None = None, target_chapter_id: str | None = None) -> WorldToNovelPreview:
        draft_id = f"wn_{target_chapter_id or 'chapter'}_{len(safe_event_summaries)}"
        draft = CrossModeDraft(
            artifact_id=draft_id,
            project_id=project_id,
            direction=CrossModeDirection.WORLD_TO_NOVEL,
            source_refs=[f"world:event:{item}" for item in source_event_ids or []],
            target_refs=[f"novel:chapter:{target_chapter_id}"] if target_chapter_id else [],
            artifact_type="chapter_draft",
            proposed_content={"safe_event_summaries": [redact_text(item) for item in safe_event_summaries]},
            validation_status="valid",
        )
        self.repository.create_draft(draft)
        return WorldToNovelPreview(draft_id=draft_id, source_event_ids=source_event_ids or [], safe_event_summaries=[redact_text(item) for item in safe_event_summaries], suggested_chapter_title="World Event Chapter", draft_summary=" ".join(safe_event_summaries[:2]), draft_text="\n\n".join(safe_event_summaries) if safe_event_summaries else None)


class TavernToWorldApplyService:
    def __init__(self, repository: CrossModeRepository) -> None:
        self.repository = repository

    def build_apply_plan(self, proposal: CrossModeProposal) -> CrossModeApplyPlan:
        plan = CrossModeApplyPlan(
            apply_plan_id=f"apply_{proposal.proposal_id}",
            project_id=proposal.project_id,
            proposal_id=proposal.proposal_id,
            apply_target="world_save",
            requires_confirmation=True,
            expected_changes=["Validated StateDelta/EventLog application required."],
            validation_status="valid" if proposal.validation_status == "valid" else "warning",
        )
        self.repository.save_apply_plan(plan)
        self.repository.append_audit_record(_audit(proposal.project_id, "build_apply_plan", proposal.proposal_id, proposal.target_refs))
        return plan

    def dry_run_apply(self, plan: CrossModeApplyPlan) -> CrossModeApplyPlan:
        return plan.model_copy(update={"dry_run_result": {"ok": plan.requires_confirmation, "writes": 0}, "validation_status": "valid"})

    def apply_confirmed(self, plan: CrossModeApplyPlan, *, explicit_confirm: bool = False, state: Any | None = None, event_log: Any | None = None, state_deltas: list[Any] | None = None) -> CrossModeAuditRecord:
        if not explicit_confirm:
            raise ValueError("explicit_confirm is required")
        if not plan.requires_confirmation:
            raise ValueError("Apply plan must require confirmation")
        related_event_id: str | None = None
        if state is not None or event_log is not None or state_deltas:
            if state is None or event_log is None or not state_deltas:
                raise ValueError("state, event_log, and state_deltas are required together for World apply")
            from app.core.event_log import Event
            from app.core.state_delta import apply_delta

            next_state = state
            event_id = f"cross_mode_apply_{plan.apply_plan_id}"
            normalized_deltas = []
            for delta in state_deltas:
                normalized = delta.model_copy(update={"caused_by_event_id": delta.caused_by_event_id or event_id})
                next_state = apply_delta(next_state, normalized)
                normalized_deltas.append(normalized)
            state.__dict__.update(next_state.__dict__)
            event_log.append(
                Event(
                    event_id=event_id,
                    turn=getattr(state, "turn", 0),
                    event_type="cross_mode_apply",
                    actor_id="cross_mode",
                    action_type="apply_confirmed",
                    result="Cross-mode proposal applied through StateDelta.",
                    visible_to_player=False,
                    state_deltas=normalized_deltas,
                    visible_summary="Cross-mode proposal applied.",
                )
            )
            related_event_id = event_id
        record = _audit(plan.project_id, "confirmed_apply", plan.apply_plan_id, [], summary="Confirmed apply requested; World runtime must record EventLog.")
        record = record.model_copy(update={"related_event_id": related_event_id})
        return self.repository.append_audit_record(record)


class WorldTavernSyncDiff(BaseModel):
    diff_id: str
    project_id: str
    world_npc_ref: str
    tavern_character_ref: str | None = None
    differences: list[str] = Field(default_factory=list)
    mode: Literal["player_safe", "authoring"] = "player_safe"


class WorldTavernSyncProposal(BaseModel):
    proposal_id: str
    diff_id: str
    project_id: str
    direction: Literal["world_npc_to_tavern_character", "tavern_character_to_world_npc_draft", "compare_only"] = "compare_only"
    safe_summary: str = ""
    warnings: list[str] = Field(default_factory=list)


class WorldTavernSyncService:
    def compare_world_npc_and_tavern_character(self, *, project_id: str, npc_ref: str, tavern_character_ref: str | None = None, mode: Literal["player_safe", "authoring"] = "player_safe") -> WorldTavernSyncDiff:
        return WorldTavernSyncDiff(diff_id=f"diff_{_safe_ref_id(npc_ref)}", project_id=project_id, world_npc_ref=npc_ref, tavern_character_ref=tavern_character_ref, differences=["Draft comparison only; NPC secrets excluded."], mode=mode)

    def build_sync_proposal(self, diff: WorldTavernSyncDiff) -> WorldTavernSyncProposal:
        return WorldTavernSyncProposal(proposal_id=f"sync_{diff.diff_id}", diff_id=diff.diff_id, project_id=diff.project_id, safe_summary="Sync proposal draft; no World NPC overwrite.")


class TavernToNovelPipeline:
    def __init__(self, repository: CrossModeRepository) -> None:
        self.repository = repository

    def preview(self, *, project_id: str, session_id: str, safe_messages: list[str], target_chapter_id: str | None = None) -> CrossModeDraft:
        filtered = [item for message in safe_messages if (item := MatureExportFilter().filter_text(message, MatureExportPolicy()))]
        draft = CrossModeDraft(artifact_id=f"tn_{session_id}", project_id=project_id, direction=CrossModeDirection.TAVERN_TO_NOVEL, source_refs=[f"tavern:session:{session_id}"], target_refs=[f"novel:chapter:{target_chapter_id}"] if target_chapter_id else [], artifact_type="novel_scene_draft", proposed_content={"safe_messages": [redact_text(item) for item in filtered]}, validation_status="valid")
        return self.repository.create_draft(draft)


class NovelCharacterToTavernPipeline:
    def __init__(self, repository: CrossModeRepository) -> None:
        self.repository = repository

    def create_character_draft(self, *, project_id: str, character_profile_id: str, mode: Literal["safe", "authoring"] = "safe") -> CrossModeDraft:
        content = {"tavern_character_id": character_profile_id, "source_character_profile_id": character_profile_id, "mode": mode}
        draft = CrossModeDraft(artifact_id=f"nt_{character_profile_id}", project_id=project_id, direction=CrossModeDirection.NOVEL_TO_TAVERN, source_refs=[f"character:{character_profile_id}"], target_refs=[f"tavern:character:{character_profile_id}"], artifact_type="tavern_character_draft", proposed_content=content, validation_status="valid")
        return self.repository.create_draft(draft)


def validate_cross_mode_project(project_root: str | Path, *, profile: Literal["normal", "debug"] = "normal") -> CrossModeValidationReport:
    return CrossModeValidationService(project_root).validate(profile=profile)


def _audit(project_id: str, action: str, source_id: str | None, refs: list[str], *, result: CrossModeAuditResult = CrossModeAuditResult.SUCCESS, summary: str | None = None) -> CrossModeAuditRecord:
    return CrossModeAuditRecord(audit_id=f"audit_{action}_{source_id or now_iso().replace(':', '_').replace('.', '_')}", project_id=project_id, action_type=action, source_artifact_id=source_id, target_refs=refs, safe_summary=summary or f"{action} recorded.", result=result)


def _issue(severity: Literal["suggestion", "warning", "error", "blocker"], code: str, message: str, artifact_ref: str, **details: str) -> CrossModeValidationIssue:
    return CrossModeValidationIssue(severity=severity, code=code, message=redact_text(message), artifact_ref=artifact_ref, safe_details={key: redact_text(value) for key, value in details.items()})


def _safe_ref_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)[:96].strip("._-")
    return cleaned or "artifact"


def _redact_obj(value: Any) -> Any:
    if isinstance(value, str):
        text = redact_text(value)
        lowered = text.lower()
        if "hidden" in lowered or "debug" in lowered or "state_delta" in lowered:
            return "[redacted]"
        return text
    if isinstance(value, list):
        return [_redact_obj(item) for item in value]
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in ("secret", "api_key", "hidden", "debug", "state_delta", "raw_delta")):
                continue
            safe[str(key)] = _redact_obj(item)
        return safe
    return value
