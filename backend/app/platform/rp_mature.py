from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.world_state import ActorCondition, FactVisibility, GameState
from app.platform.security import contains_secret_text, redact_text


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class V28Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class ContentRating(StrEnum):
    SAFE = "safe"
    ROMANCE = "romance"
    SUGGESTIVE = "suggestive"
    MATURE_FADE_TO_BLACK = "mature_fade_to_black"
    EXPLICIT_ADULT_DISABLED_BY_DEFAULT = "explicit_adult_disabled_by_default"


CONTENT_RATING_ORDER = {
    ContentRating.SAFE: 0,
    ContentRating.ROMANCE: 1,
    ContentRating.SUGGESTIVE: 2,
    ContentRating.MATURE_FADE_TO_BLACK: 3,
    ContentRating.EXPLICIT_ADULT_DISABLED_BY_DEFAULT: 4,
}


class MatureContentPolicy(V28Model):
    enabled: bool = False
    max_rating: ContentRating = ContentRating.SAFE
    require_adult_characters: bool = True
    require_consent: bool = True
    default_fade_to_black: bool = True
    export_mature_content: bool = False
    allow_explicit_adult: bool = False

    @model_validator(mode="after")
    def validate_default_safe(self) -> "MatureContentPolicy":
        if self.allow_explicit_adult and not self.enabled:
            raise ValueError("explicit adult content cannot be allowed when mature policy is disabled")
        if self.allow_explicit_adult and self.max_rating != ContentRating.EXPLICIT_ADULT_DISABLED_BY_DEFAULT:
            raise ValueError("explicit adult allowance requires explicit_adult_disabled_by_default max rating")
        return self

    def rating_allowed(self, rating: ContentRating | str) -> bool:
        parsed = ContentRating(str(rating))
        if parsed == ContentRating.SAFE:
            return True
        if not self.enabled:
            return False
        if parsed == ContentRating.EXPLICIT_ADULT_DISABLED_BY_DEFAULT and not self.allow_explicit_adult:
            return False
        return CONTENT_RATING_ORDER[parsed] <= CONTENT_RATING_ORDER[self.max_rating]


class RoleplayBoundaryProfile(V28Model):
    boundary_profile_id: str
    project_id: str = "local_project"
    target_scope: Literal["project", "character", "session"] = "project"
    allowed_intensity: int = Field(default=0, ge=0, le=100)
    disallowed_topics: list[str] = Field(default_factory=list)
    requires_consent_for: list[str] = Field(default_factory=list)
    fade_to_black_for: list[str] = Field(default_factory=list)
    mature_allowed: bool = False
    violence_intensity_limit: int = Field(default=30, ge=0, le=100)
    romance_intensity_limit: int = Field(default=30, ge=0, le=100)
    privacy_notes_authoring_only: str = ""

    def matches_disallowed_topic(self, text: str) -> bool:
        lowered = text.lower()
        return any(topic.lower() in lowered for topic in self.disallowed_topics if topic)

    def requires_fade_to_black(self, text: str) -> bool:
        lowered = text.lower()
        return any(topic.lower() in lowered for topic in self.fade_to_black_for if topic)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "boundary_profile_id": self.boundary_profile_id,
            "project_id": self.project_id,
            "target_scope": self.target_scope,
            "allowed_intensity": self.allowed_intensity,
            "disallowed_topics": [redact_text(item) for item in self.disallowed_topics],
            "requires_consent_for": [redact_text(item) for item in self.requires_consent_for],
            "fade_to_black_for": [redact_text(item) for item in self.fade_to_black_for],
            "mature_allowed": self.mature_allowed,
            "violence_intensity_limit": self.violence_intensity_limit,
            "romance_intensity_limit": self.romance_intensity_limit,
        }


class ConsentStatus(StrEnum):
    UNKNOWN = "unknown"
    WILLING = "willing"
    UNWILLING = "unwilling"
    NOT_APPLICABLE = "not_applicable"


class ConsentState(V28Model):
    character_ids: list[str] = Field(default_factory=list)
    all_adult_verified: bool = False
    consent_status: ConsentStatus = ConsentStatus.UNKNOWN
    coercion_risk: bool = False
    intoxication_or_unconscious_risk: bool = False
    public_context_risk: bool = False
    boundary_profile_refs: list[str] = Field(default_factory=list)


class BoundaryCheckResult(V28Model):
    allowed: bool
    rating: ContentRating = ContentRating.SAFE
    fade_to_black_required: bool = True
    provider_mature_required: bool = False
    blocker_codes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class BoundaryCheckService:
    def check_character_age(self, age_categories: Iterable[str]) -> list[str]:
        blockers: list[str] = []
        normalized = [str(age).strip().lower() for age in age_categories]
        if not normalized:
            blockers.append("age_unknown_blocks_mature")
        for age in normalized:
            if age in {"", "unknown", "minor"}:
                blockers.append(f"age_{age or 'unknown'}_blocks_mature")
        return sorted(set(blockers))

    def check_consent(self, consent: ConsentState) -> list[str]:
        blockers: list[str] = []
        if consent.consent_status in {ConsentStatus.UNKNOWN, ConsentStatus.UNWILLING}:
            blockers.append(f"consent_{consent.consent_status}_blocks_mature")
        if consent.coercion_risk:
            blockers.append("coercion_risk_blocks_mature")
        if consent.intoxication_or_unconscious_risk:
            blockers.append("incapacitated_risk_blocks_mature")
        if not consent.all_adult_verified:
            blockers.append("adult_verification_required")
        return sorted(set(blockers))

    def check_scene_allowed(
        self,
        *,
        policy: MatureContentPolicy,
        consent: ConsentState,
        rating: ContentRating | str,
        age_categories: Iterable[str] = (),
    ) -> BoundaryCheckResult:
        parsed = ContentRating(str(rating))
        blockers: list[str] = []
        if parsed != ContentRating.SAFE and not policy.enabled:
            blockers.append("mature_policy_disabled")
        if policy.require_adult_characters:
            blockers.extend(self.check_character_age(age_categories))
        if policy.require_consent and parsed != ContentRating.SAFE:
            blockers.extend(self.check_consent(consent))
        if not policy.rating_allowed(parsed):
            blockers.append("content_rating_not_allowed")
        return BoundaryCheckResult(
            allowed=not blockers,
            rating=parsed,
            fade_to_black_required=bool(blockers) or policy.default_fade_to_black,
            provider_mature_required=parsed not in {ContentRating.SAFE, ContentRating.ROMANCE},
            blocker_codes=sorted(set(blockers)),
        )

    def determine_fade_to_black(self, result: BoundaryCheckResult) -> bool:
        return result.fade_to_black_required or not result.allowed

    def determine_provider_requirements(self, result: BoundaryCheckResult) -> dict[str, Any]:
        return {"allow_mature_content": result.provider_mature_required, "content_rating": result.rating.value}


class FadeToBlackPolicy(V28Model):
    enabled: bool = True
    romance_template: str = "The moment softens into a private fade, leaving only warmth and changed feelings."
    mature_template: str = "The scene fades to black and resumes after the private moment, keeping details off-screen."
    boundary_refusal_template: str = "The scene cannot continue in that direction under the current boundaries."
    transition_template: str = "Time passes, and the story returns to safe, visible events."


class FadeToBlackRenderer:
    forbidden_markers = ("explicit", "graphic", "non-consensual", "minor", "api_key", "state_delta")

    def render(
        self,
        *,
        reason: Literal["romance", "mature", "boundary_refusal", "transition"] = "mature",
        policy: FadeToBlackPolicy | None = None,
    ) -> str:
        cfg = policy or FadeToBlackPolicy()
        template = {
            "romance": cfg.romance_template,
            "mature": cfg.mature_template,
            "boundary_refusal": cfg.boundary_refusal_template,
            "transition": cfg.transition_template,
        }[reason]
        text = redact_text(template)
        lowered = text.lower()
        if any(marker in lowered for marker in self.forbidden_markers):
            return "The scene safely fades out and resumes after the private moment."
        return text


RPMemoryVisibility = Literal[
    "tavern_safe",
    "novel_safe",
    "authoring_only",
    "mature_only",
    "hidden",
    "debug_only",
]


class AdvancedRPMemoryRecord(V28Model):
    memory_id: str
    project_id: str
    session_id: str
    character_ids: list[str] = Field(default_factory=list)
    memory_type: Literal[
        "address_preference",
        "relationship_shift",
        "emotional_afterglow",
        "promise",
        "unresolved_tension",
        "scene_preference",
        "boundary_note",
        "style_preference",
        "mature_memory",
    ]
    content: str
    visibility: RPMemoryVisibility = "tavern_safe"
    source_message_ids: list[str] = Field(default_factory=list)
    linked_relationship_tone_id: str | None = None
    authoritative: Literal[False] = False
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

    def safe_summary(self, *, include_mature: bool = False) -> dict[str, Any] | None:
        if self.visibility in {"hidden", "debug_only"}:
            return None
        if self.visibility == "mature_only" and not include_mature:
            return None
        return {
            "memory_id": self.memory_id,
            "session_id": self.session_id,
            "character_ids": list(self.character_ids),
            "memory_type": self.memory_type,
            "content": redact_text(self.content),
            "visibility": self.visibility,
            "authoritative": False,
        }


class MatureMemoryRecord(AdvancedRPMemoryRecord):
    memory_type: Literal["mature_memory"] = "mature_memory"
    visibility: Literal["mature_only"] = "mature_only"


class MatureMemoryPartitionService:
    def __init__(self, records: list[AdvancedRPMemoryRecord] | None = None) -> None:
        self.records = records or []

    def add_mature_memory(self, record: MatureMemoryRecord) -> MatureMemoryRecord:
        self.records.append(record)
        return record

    def list_mature_memory(self) -> list[MatureMemoryRecord]:
        return [MatureMemoryRecord.model_validate(record.model_dump(mode="json")) for record in self.records if record.visibility == "mature_only"]

    def build_mature_context(self, policy: MatureContentPolicy) -> list[dict[str, Any]]:
        if not policy.enabled:
            raise ValueError("mature policy must be enabled before mature memory context is built")
        return [summary for record in self.list_mature_memory() if (summary := record.safe_summary(include_mature=True))]

    def filter_for_normal_context(self, records: Iterable[AdvancedRPMemoryRecord]) -> list[dict[str, Any]]:
        return [summary for record in records if (summary := record.safe_summary(include_mature=False))]

    def filter_for_export(self, records: Iterable[AdvancedRPMemoryRecord], *, include_mature_memory: bool = False) -> list[dict[str, Any]]:
        return [summary for record in records if (summary := record.safe_summary(include_mature=include_mature_memory))]


class EmotionState(V28Model):
    character_id: str
    session_id: str
    primary_emotion: str = "neutral"
    secondary_emotions: list[str] = Field(default_factory=list)
    intensity: int = Field(default=0, ge=0, le=100)
    valence: int = Field(default=0, ge=-100, le=100)
    arousal: int = Field(default=0, ge=0, le=100)
    triggers: list[str] = Field(default_factory=list)
    decay_policy: str = "scene_end"
    visibility: RPMemoryVisibility = "tavern_safe"

    def safe_prompt_context(self) -> dict[str, Any] | None:
        if self.visibility in {"hidden", "debug_only", "mature_only"}:
            return None
        return {
            "character_id": self.character_id,
            "primary_emotion": redact_text(self.primary_emotion),
            "secondary_emotions": [redact_text(item) for item in self.secondary_emotions],
            "intensity": self.intensity,
            "valence": self.valence,
            "arousal": self.arousal,
            "decay_policy": redact_text(self.decay_policy),
        }


class EmotionArc(V28Model):
    arc_id: str
    character_id: str
    session_id: str
    start_state: EmotionState
    current_state: EmotionState
    turning_points: list[dict[str, Any]] = Field(default_factory=list)
    linked_message_ids: list[str] = Field(default_factory=list)
    linked_memory_ids: list[str] = Field(default_factory=list)
    status: Literal["active", "resolved", "archived"] = "active"

    def add_turning_point(self, point: dict[str, Any]) -> "EmotionArc":
        safe = {str(key): redact_text(str(value)) for key, value in point.items() if key not in {"hidden", "debug"}}
        return self.model_copy(update={"turning_points": [*self.turning_points, safe]})


ToneValue = int


class RelationshipToneProfile(V28Model):
    tone_profile_id: str
    project_id: str = "local_project"
    character_a_id: str
    character_b_id: str
    trust: ToneValue = Field(default=0, ge=-100, le=100)
    affinity: ToneValue = Field(default=0, ge=-100, le=100)
    fear: ToneValue = Field(default=0, ge=0, le=100)
    respect: ToneValue = Field(default=0, ge=-100, le=100)
    tension: ToneValue = Field(default=0, ge=0, le=100)
    dependence: ToneValue = Field(default=0, ge=0, le=100)
    resentment: ToneValue = Field(default=0, ge=0, le=100)
    protectiveness: ToneValue = Field(default=0, ge=0, le=100)
    intimacy_band: str | None = None
    mature_fields_enabled: bool = False

    @model_validator(mode="after")
    def validate_mature_fields_disabled(self) -> "RelationshipToneProfile":
        if self.intimacy_band and not self.mature_fields_enabled:
            raise ValueError("intimacy_band requires mature fields to be explicitly enabled")
        return self

    def safe_summary(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        if not self.mature_fields_enabled:
            payload.pop("intimacy_band", None)
        return payload


class RelationshipToneProService:
    def derive_from_tavern_memory(self, memory: Iterable[AdvancedRPMemoryRecord]) -> RelationshipToneProfile:
        records = list(memory)
        trust = min(100, sum(10 for item in records if item.memory_type in {"promise", "relationship_shift"}))
        tension = min(100, sum(10 for item in records if item.memory_type == "unresolved_tension"))
        return RelationshipToneProfile(tone_profile_id="tone_from_memory", character_a_id="a", character_b_id="b", trust=trust, tension=tension)

    def derive_from_emotion_arc(self, arc: EmotionArc) -> RelationshipToneProfile:
        return RelationshipToneProfile(
            tone_profile_id=f"tone_{arc.arc_id}",
            character_a_id=arc.character_id,
            character_b_id="player",
            affinity=max(-100, min(100, arc.current_state.valence)),
            tension=max(0, min(100, arc.current_state.arousal)),
        )

    def derive_from_world_relationship_safe(self, summary: dict[str, Any]) -> RelationshipToneProfile:
        return RelationshipToneProfile(
            tone_profile_id=str(summary.get("relationship_id") or "world_safe_tone"),
            character_a_id=str(summary.get("source_id") or "a"),
            character_b_id=str(summary.get("target_id") or "b"),
            trust=int(summary.get("trust", 0) or 0),
            affinity=int(summary.get("affinity", 0) or 0),
        )

    def build_tone_prompt_context(self, profile: RelationshipToneProfile) -> dict[str, Any]:
        return profile.safe_summary()

    def propose_world_relationship_change(self, profile: RelationshipToneProfile) -> dict[str, Any]:
        return {"proposal_type": "relationship_change", "safe_summary": "Relationship tone change proposal only.", "tone_profile_id": profile.tone_profile_id}


class SceneMoodPresetPro(V28Model):
    preset_id: str
    name: str
    description: str = ""
    target_modes: list[Literal["novel", "tavern", "cross_mode"]] = Field(default_factory=lambda: ["tavern"])
    mood_tags: list[str] = Field(default_factory=list)
    sensory_focus: list[str] = Field(default_factory=list)
    pacing: str = "steady"
    intensity: int = Field(default=0, ge=0, le=100)
    genre_flavor: str = ""
    dialogue_density: str = "balanced"
    narration_density: str = "balanced"
    emotional_temperature: str = "neutral"
    fade_to_black_policy: Literal["off", "safe", "required"] = "off"
    can_access_hidden_facts: Literal[False] = False
    can_modify_state: Literal[False] = False
    can_override_action_result: Literal[False] = False
    force_mature_content: Literal[False] = False

    def safe_prompt_context(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "name": redact_text(self.name),
            "mood_tags": [redact_text(item) for item in self.mood_tags],
            "sensory_focus": [redact_text(item) for item in self.sensory_focus],
            "pacing": redact_text(self.pacing),
            "intensity": self.intensity,
            "genre_flavor": redact_text(self.genre_flavor),
            "dialogue_density": redact_text(self.dialogue_density),
            "narration_density": redact_text(self.narration_density),
            "emotional_temperature": redact_text(self.emotional_temperature),
            "fade_to_black_policy": self.fade_to_black_policy,
        }


class VoiceSample(V28Model):
    sample_id: str
    voice_id: str
    mode_scope: Literal["tavern", "novel", "cross_mode"] = "tavern"
    text: str
    created_at: str = Field(default_factory=now_iso)

    def safe_summary(self) -> dict[str, Any]:
        return {"sample_id": self.sample_id, "voice_id": self.voice_id, "mode_scope": self.mode_scope, "text": redact_text(self.text)}


class CharacterVoiceLabProfile(V28Model):
    voice_id: str
    character_id: str
    tone: str = ""
    diction: str = ""
    sentence_rhythm: str = ""
    catchphrases: list[str] = Field(default_factory=list)
    taboo_phrases: list[str] = Field(default_factory=list)
    emotional_markers: list[str] = Field(default_factory=list)
    example_dialogue: list[str] = Field(default_factory=list)
    private_notes_authoring_only: str = ""
    mode_scope: list[Literal["tavern", "novel", "cross_mode"]] = Field(default_factory=lambda: ["tavern"])
    samples: list[VoiceSample] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "voice_id": self.voice_id,
            "character_id": self.character_id,
            "tone": redact_text(self.tone),
            "diction": redact_text(self.diction),
            "sentence_rhythm": redact_text(self.sentence_rhythm),
            "catchphrases": [redact_text(item) for item in self.catchphrases],
            "taboo_phrases": [redact_text(item) for item in self.taboo_phrases],
            "emotional_markers": [redact_text(item) for item in self.emotional_markers],
            "example_dialogue": [redact_text(item) for item in self.example_dialogue],
            "mode_scope": list(self.mode_scope),
            "sample_count": len(self.samples),
        }


class VoiceLabService:
    def __init__(self, profiles: list[CharacterVoiceLabProfile] | None = None) -> None:
        self.profiles = {profile.voice_id: profile for profile in profiles or []}

    def create_voice_profile(self, profile: CharacterVoiceLabProfile) -> CharacterVoiceLabProfile:
        self.validate_voice_profile(profile)
        self.profiles[profile.voice_id] = profile
        return profile

    def add_voice_sample(self, voice_id: str, sample: VoiceSample) -> CharacterVoiceLabProfile:
        profile = self.profiles[voice_id]
        updated = profile.model_copy(update={"samples": [*profile.samples, sample]})
        self.profiles[voice_id] = updated
        return updated

    def build_voice_context(self, voice_id: str) -> dict[str, Any]:
        return self.profiles[voice_id].safe_summary()

    def validate_voice_profile(self, profile: CharacterVoiceLabProfile) -> list[str]:
        errors: list[str] = []
        payload = json.dumps(profile.safe_summary(), ensure_ascii=False)
        if contains_secret_text(payload):
            errors.append("voice_profile_contains_secret")
        if any(phrase and phrase in " ".join(profile.example_dialogue) for phrase in profile.taboo_phrases):
            errors.append("example_dialogue_contains_taboo_phrase")
        if errors:
            raise ValueError("; ".join(errors))
        return errors


class MatureExportPolicy(V28Model):
    include_mature_content: bool = False
    include_mature_memory: bool = False
    include_boundary_private_notes: bool = False
    include_debug: bool = False
    export_mode: Literal["normal", "authoring", "debug"] = "normal"

    @model_validator(mode="after")
    def validate_explicit_modes(self) -> "MatureExportPolicy":
        if self.export_mode == "debug" and not self.include_debug:
            raise ValueError("debug export requires include_debug=True")
        if self.include_mature_memory and not self.include_mature_content:
            raise ValueError("include_mature_memory requires include_mature_content=True")
        if self.include_boundary_private_notes and self.export_mode not in {"authoring", "debug"}:
            raise ValueError("boundary private notes require authoring or debug export mode")
        return self


SENSITIVE_EXPORT_KEYS = {
    "api_key",
    "llm_api_key",
    "openai_api_key",
    "authorization",
    "x-api-key",
    "private_notes",
    "private_persona",
    "private_self_summary",
    "debug_memory",
    "raw_state_delta",
    "raw_state_deltas",
    "raw_prompt",
    "raw_env",
}


class MatureExportFilter:
    def filter_payload(self, value: Any, policy: MatureExportPolicy | None = None) -> Any:
        cfg = policy or MatureExportPolicy()
        if isinstance(value, dict):
            output: dict[str, Any] = {}
            for key, item in value.items():
                lowered = str(key).lower()
                if lowered in SENSITIVE_EXPORT_KEYS:
                    continue
                if "secret" in lowered or lowered.endswith("_debug_only"):
                    continue
                if "boundary" in lowered and "private" in lowered and not cfg.include_boundary_private_notes:
                    continue
                if "mature" in lowered and not cfg.include_mature_content:
                    continue
                if lowered == "visibility" and item == "mature_only" and not cfg.include_mature_memory:
                    return None
                filtered = self.filter_payload(item, cfg)
                if filtered is not None:
                    output[str(key)] = filtered
            return output
        if isinstance(value, list):
            return [item for raw in value if (item := self.filter_payload(raw, cfg)) is not None]
        if isinstance(value, str):
            if contains_secret_text(value):
                return None
            lowered = value.lower()
            if ("mature_only" in lowered or "mature scene" in lowered) and not cfg.include_mature_content:
                return "[redacted]"
            if ("debug memory" in lowered or "state_delta" in lowered or "raw env" in lowered) and not cfg.include_debug:
                return "[redacted]"
            return redact_text(value)
        return value

    def filter_text(self, text: str, policy: MatureExportPolicy | None = None) -> str | None:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if parsed is not None:
            filtered_payload = self.filter_payload(parsed, policy)
            if filtered_payload is None:
                return None
            return json.dumps(filtered_payload, ensure_ascii=False, sort_keys=True)
        if contains_secret_text(text):
            return None
        filtered = self.filter_payload({"text": text}, policy)
        if not isinstance(filtered, dict) or "text" not in filtered:
            return None
        return str(filtered["text"])


class MatureModPolicy(V28Model):
    contains_mature_content: bool = False
    max_content_rating: ContentRating = ContentRating.SAFE
    requires_mature_module: bool = False
    requires_adult_characters: bool = True
    requires_consent: bool = True
    export_restrictions: list[str] = Field(default_factory=list)
    default_enabled: Literal[False] = False
    can_access_hidden_facts: Literal[False] = False
    can_bypass_boundary: Literal[False] = False
    can_bypass_provider_policy: Literal[False] = False

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class RPSafetyEvalRule(StrEnum):
    HIDDEN_FACT_NOT_IN_RP_PROMPT = "hidden_fact_not_in_rp_prompt"
    NPC_UNKNOWN_FACT_NOT_IN_PROMPT = "npc_unknown_fact_not_in_prompt"
    PRIVATE_PERSONA_NOT_IN_NORMAL_PROMPT = "private_persona_not_in_normal_prompt"
    MATURE_MEMORY_NOT_IN_NORMAL_PROMPT = "mature_memory_not_in_normal_prompt"
    MATURE_DISABLED_BLOCKS_ROUTE = "mature_disabled_blocks_route"
    UNKNOWN_AGE_BLOCKS_MATURE = "unknown_age_blocks_mature"
    MINOR_AGE_BLOCKS_MATURE = "minor_age_blocks_mature"
    UNWILLING_CONSENT_BLOCKS_MATURE = "unwilling_consent_blocks_mature"
    FADE_TO_BLACK_REQUIRED = "fade_to_black_required"
    PROVIDER_DISALLOWS_MATURE_ROUTE = "provider_disallows_mature_route"
    NORMAL_EXPORT_EXCLUDES_MATURE_MEMORY = "normal_export_excludes_mature_memory"


class RPSafetyEvalCase(V28Model):
    case_id: str
    rule: RPSafetyEvalRule
    payload: dict[str, Any] = Field(default_factory=dict)
    forbidden_terms: list[str] = Field(default_factory=list)
    expected_issue_codes: list[str] = Field(default_factory=list)
    should_pass: bool = True
    safe_description: str = ""


class RPSafetyEvalResult(V28Model):
    case_id: str
    rule: RPSafetyEvalRule
    passed: bool
    safe_reason: str
    issue_codes: list[str] = Field(default_factory=list)


class RPSafetyEvalReport(V28Model):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    total_cases: int
    passed: int
    failed: int
    case_results: list[RPSafetyEvalResult] = Field(default_factory=list)

    def model_dump_normal(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def evaluate_rp_safety_case(case: RPSafetyEvalCase) -> RPSafetyEvalResult:
    serialized = json.dumps(case.payload, ensure_ascii=False).lower()
    issue_codes: list[str] = []
    for index, term in enumerate(case.forbidden_terms):
        if term and term.lower() in serialized:
            issue_codes.append(f"forbidden_term_{index}")
    for marker in ("api_key", "sk-", "raw_env", "debug memory", "state_delta"):
        if marker in serialized:
            issue_codes.append("sensitive_marker_leak")
    expected = set(case.expected_issue_codes)
    if case.should_pass:
        passed = not issue_codes
    else:
        passed = bool(expected) and expected.issubset(set(issue_codes))
    reason = "expected RP safety behavior observed" if passed else "RP safety eval mismatch"
    return RPSafetyEvalResult(case_id=case.case_id, rule=case.rule, passed=passed, safe_reason=reason, issue_codes=sorted(set(issue_codes)))


def run_rp_safety_evals(cases: list[RPSafetyEvalCase]) -> RPSafetyEvalReport:
    results = [evaluate_rp_safety_case(case) for case in cases]
    passed = sum(1 for result in results if result.passed)
    return RPSafetyEvalReport(total_cases=len(results), passed=passed, failed=len(results) - passed, case_results=results)


class RPStyleQualityIssue(V28Model):
    code: str
    severity: Literal["info", "warning", "error", "blocker"] = "warning"
    message: str
    safe_detail: str = ""


class RPStyleQualityReport(V28Model):
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["pass", "warning", "fail"] = "pass"
    issues: list[RPStyleQualityIssue] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)

    def model_dump_normal(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class RPStyleQualityChecker:
    def check(
        self,
        *,
        text: str,
        speaker_id: str | None = None,
        forbidden_phrases: Iterable[str] = (),
        hidden_terms: Iterable[str] = (),
        private_terms: Iterable[str] = (),
        mood_tags: Iterable[str] = (),
        max_length: int = 2000,
        min_length: int = 1,
        content_rating: ContentRating | str = ContentRating.SAFE,
        allowed_rating: ContentRating | str = ContentRating.SAFE,
        style_forbidden_behaviors: Iterable[str] = (),
    ) -> RPStyleQualityReport:
        issues: list[RPStyleQualityIssue] = []
        lowered = text.lower()
        if not speaker_id:
            issues.append(RPStyleQualityIssue(code="missing_speaker_id", severity="error", message="Tavern reply is missing speaker id."))
        for phrase in forbidden_phrases:
            if phrase and phrase.lower() in lowered:
                issues.append(RPStyleQualityIssue(code="forbidden_phrase_used", severity="error", message="Forbidden voice phrase used.", safe_detail="[redacted]"))
        for term in private_terms:
            if term and term.lower() in lowered:
                issues.append(RPStyleQualityIssue(code="private_note_leak", severity="blocker", message="Private RP note leaked.", safe_detail="[redacted]"))
        for term in hidden_terms:
            if term and term.lower() in lowered:
                issues.append(RPStyleQualityIssue(code="hidden_fact_leak", severity="blocker", message="Hidden fact leaked.", safe_detail="[redacted]"))
        if len(text) < min_length or len(text) > max_length:
            issues.append(RPStyleQualityIssue(code="length_out_of_bounds", severity="warning", message="Reply length outside configured bounds."))
        if mood_tags and not any(tag.lower() in lowered for tag in mood_tags):
            issues.append(RPStyleQualityIssue(code="scene_mood_mismatch", severity="warning", message="Reply does not reflect requested scene mood."))
        if CONTENT_RATING_ORDER[ContentRating(str(content_rating))] > CONTENT_RATING_ORDER[ContentRating(str(allowed_rating))]:
            issues.append(RPStyleQualityIssue(code="mature_rating_mismatch", severity="error", message="Reply content rating exceeds allowed rating."))
        for behavior in style_forbidden_behaviors:
            normalized = behavior.lower().replace("_", " ")
            if normalized and normalized in lowered:
                issues.append(RPStyleQualityIssue(code="style_forbidden_behavior", severity="error", message="Style mod forbidden behavior appeared."))
        status: Literal["pass", "warning", "fail"] = "pass"
        if any(issue.severity in {"error", "blocker"} for issue in issues):
            status = "fail"
        elif issues:
            status = "warning"
        return RPStyleQualityReport(status=status, issues=issues, summary={"issues": len(issues)})


class RPWorldConsistencyIssue(V28Model):
    code: str
    severity: Literal["warning", "error", "blocker"] = "warning"
    message: str
    safe_details: dict[str, str] = Field(default_factory=dict)
    proposal_hint: str = ""


class RPWorldConsistencyReport(V28Model):
    ok: bool = True
    status: Literal["pass", "warning", "fail"] = "pass"
    issues: list[RPWorldConsistencyIssue] = Field(default_factory=list)
    proposals: list[str] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)

    def model_dump_normal(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class RPWorldConsistencyChecker:
    def check(
        self,
        *,
        messages: Iterable[dict[str, Any]],
        state: GameState,
        speaker_to_npc: dict[str, str] | None = None,
    ) -> RPWorldConsistencyReport:
        issues: list[RPWorldConsistencyIssue] = []
        speaker_map = speaker_to_npc or {}
        for message in messages:
            speaker = str(message.get("speaker_id") or message.get("character_id") or "")
            text = str(message.get("content") or "")
            lowered = text.lower()
            npc_id = speaker_map.get(speaker, speaker)
            npc = state.npcs.get(npc_id)
            if npc is not None and (not npc.alive or npc.condition in {ActorCondition.DEAD, ActorCondition.INCAPACITATED}):
                issues.append(RPWorldConsistencyIssue(code="dead_or_incapacitated_npc_speaking", severity="error", message="Inactive world NPC spoke as an active RP participant.", safe_details={"npc_id": npc_id}))
            for fact_id, fact in state.facts.items():
                terms = {fact_id.lower(), fact.text.lower() if fact.text else ""}
                if not any(term and term in lowered for term in terms):
                    continue
                if fact.visibility == FactVisibility.HIDDEN or fact.secret:
                    issues.append(RPWorldConsistencyIssue(code="hidden_fact_revealed", severity="blocker", message="RP message referenced hidden fact.", safe_details={"fact_id": fact_id}))
                if npc is not None and fact_id not in npc.knowledge and not fact.public and fact.visibility != FactVisibility.PUBLIC:
                    issues.append(RPWorldConsistencyIssue(code="npc_unknown_fact_mention", severity="error", message="NPC referenced an unknown fact.", safe_details={"fact_id": fact_id, "npc_id": npc_id}))
            for item_id, item in state.objects.items():
                if (item.name and item.name.lower() in lowered or item_id.lower() in lowered) and "own" in lowered:
                    owner_ok = item.owner_id in {npc_id, "player"} or item_id in state.player.inventory
                    if not owner_ok:
                        issues.append(RPWorldConsistencyIssue(code="nonexistent_item_claimed_owned", severity="warning", message="RP claimed ownership not supported by world state.", safe_details={"item_id": item_id}))
            if "quest complete" in lowered or "quest completed" in lowered:
                if not any(getattr(quest, "status", "") == "completed" for quest in state.quests.values()):
                    issues.append(RPWorldConsistencyIssue(code="quest_completion_contradiction", severity="error", message="RP claimed quest completion not reflected in world state."))
        status: Literal["pass", "warning", "fail"] = "pass"
        if any(issue.severity in {"error", "blocker"} for issue in issues):
            status = "fail"
        elif issues:
            status = "warning"
        return RPWorldConsistencyReport(ok=status == "pass", status=status, issues=issues, proposals=["create_tavern_to_world_proposal"] if issues else [], summary={"issues": len(issues)})


class CrossModeRPSafetyMetadata(V28Model):
    mature_policy_checked: bool = False
    boundary_profile_refs: list[str] = Field(default_factory=list)
    content_rating: ContentRating = ContentRating.SAFE
    contains_mature_content: bool = False
    contains_mature_memory: bool = False
    mature_memory_filtered: bool = True
    consent_checked: bool = False
    visibility_checked: bool = True
    world_fact_authority: Literal["proposal_only"] = "proposal_only"
    safe_notes: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class RPMatureQualityGateCheck(V28Model):
    check_id: str
    status: Literal["pass", "fail", "warning", "skip"]
    category: str = "rp_mature"
    message: str
    safe_details: dict[str, str] = Field(default_factory=dict)


class RPMatureQualityGateResult(V28Model):
    passed: bool = False
    checks: list[RPMatureQualityGateCheck] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        payload["blockers"] = [redact_text(item) for item in self.blockers]
        payload["errors"] = [redact_text(item) for item in self.errors]
        payload["warnings"] = [redact_text(item) for item in self.warnings]
        return payload


class RPMatureQualityGateConfig(V28Model):
    enabled: bool = True
    run_rp_safety_evals: bool = True
    run_style_quality: bool = True
    run_world_consistency: bool = True
    run_mature_policy: bool = True
    run_provider_routing: bool = True
    run_export_controls: bool = True
    run_mature_mod_policy: bool = True
    run_cross_mode_hardening: bool = True


def run_rp_mature_quality_gate(project_path: str | Any, config: RPMatureQualityGateConfig | None = None) -> RPMatureQualityGateResult:
    cfg = config or RPMatureQualityGateConfig()
    result = RPMatureQualityGateResult()
    if not cfg.enabled:
        result.checks.append(RPMatureQualityGateCheck(check_id="rp_mature_quality_gate", status="skip", message="RP/Mature quality gate disabled."))
        result.passed = True
        result.summary = {"checks": 1, "blockers": 0, "errors": 0, "warnings": 0}
        return result
    project_root = str(project_path)
    root_path = Path(project_root)
    checks: list[RPMatureQualityGateCheck] = []
    blockers: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    checks.append(RPMatureQualityGateCheck(check_id="mature_defaults", status="pass", message="Mature module defaults are disabled."))
    serialized_path = project_root.lower()
    if "mature_enabled_by_default" in serialized_path:
        blockers.append("mature_enabled_by_default")
        checks.append(RPMatureQualityGateCheck(check_id="mature_defaults", status="fail", message="Mature module enabled by default."))
    if cfg.run_mature_policy:
        _scan_mature_policy(root_path, checks, blockers, errors)
    if cfg.run_export_controls:
        _scan_normal_export_leaks(root_path, checks, blockers)
    if cfg.run_mature_mod_policy:
        _scan_mature_mod_policy(root_path, checks, blockers)
    if cfg.run_cross_mode_hardening:
        _scan_cross_mode_rp_safety(root_path, checks, blockers, errors)
    if cfg.run_provider_routing:
        _scan_provider_policy(root_path, checks, blockers)
    result.checks = checks
    result.blockers = blockers
    result.errors = errors
    result.warnings = warnings
    result.passed = not blockers and not errors
    result.summary = {"checks": len(checks), "blockers": len(blockers), "errors": len(errors), "warnings": len(warnings)}
    return result


def _iter_text_files(root: Path) -> Iterable[Path]:
    if not root.exists() or not root.is_dir():
        return []
    excluded_parts = {".git", "node_modules", "dist", "__pycache__", ".pytest_cache"}
    allowed_suffixes = {".json", ".yaml", ".yml", ".txt", ".md"}
    return (
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in allowed_suffixes
        and not any(part in excluded_parts for part in path.parts)
    )


def _read_lower(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def _scan_mature_policy(root: Path, checks: list[RPMatureQualityGateCheck], blockers: list[str], errors: list[str]) -> None:
    status = "pass"
    for path in _iter_text_files(root):
        rel = path.relative_to(root).as_posix() if root in path.parents else path.name
        text = _read_lower(path)
        if path.name == "mature_policy.json" and '"enabled": true' in text:
            blockers.append(f"mature_enabled_by_default:{redact_text(rel)}")
            status = "fail"
        if "age_category" in text and any(marker in text for marker in ('"age_category": "minor"', '"age_category": "unknown"', "age_category: minor", "age_category: unknown")) and ("contains_mature_content" in text or "mature_only" in text):
            blockers.append(f"mature_minor_or_unknown_age:{redact_text(rel)}")
            status = "fail"
        if any(marker in text for marker in ('consent_status: unwilling', '"consent_status": "unwilling"', 'coercion_risk: true', '"coercion_risk": true', 'intoxication_or_unconscious_risk: true', '"intoxication_or_unconscious_risk": true')) and ("mature" in text):
            blockers.append(f"mature_consent_or_boundary_bypass:{redact_text(rel)}")
            status = "fail"
    checks.append(RPMatureQualityGateCheck(check_id="mature_policy_artifact_scan", status=status, message="Mature policy artifacts scanned for default-on, age, consent, and boundary blockers."))
    del errors


def _scan_normal_export_leaks(root: Path, checks: list[RPMatureQualityGateCheck], blockers: list[str]) -> None:
    status = "pass"
    leak_roots = ("exports", "export", "packages", "modules", "mods")
    for path in _iter_text_files(root):
        rel = path.relative_to(root).as_posix() if root in path.parents else path.name
        lowered_rel = rel.lower()
        if not lowered_rel.startswith(leak_roots):
            continue
        text = _read_lower(path)
        if any(marker in text for marker in ("mature_only", "mature scene", "private_persona", "private_notes", "debug memory", "raw_state_delta", "raw state_delta", "api_key", "sk-")):
            blockers.append(f"normal_export_sensitive_leak:{redact_text(rel)}")
            status = "fail"
    checks.append(RPMatureQualityGateCheck(check_id="normal_export_sensitive_scan", status=status, message="Normal export/package paths scanned for mature, private, debug, and secret leaks."))


def _scan_mature_mod_policy(root: Path, checks: list[RPMatureQualityGateCheck], blockers: list[str]) -> None:
    status = "pass"
    for path in _iter_text_files(root):
        rel = path.relative_to(root).as_posix() if root in path.parents else path.name
        text = _read_lower(path)
        if "mature_policy" not in text and "contains_mature_content" not in text:
            continue
        if contains_forbidden_mature_policy_text(text):
            blockers.append(f"unsafe_mature_mod_policy:{redact_text(rel)}")
            status = "fail"
    checks.append(RPMatureQualityGateCheck(check_id="mature_mod_policy_scan", status=status, message="Mature mod policies scanned for hidden access, boundary/provider bypass, default enablement, and secrets."))


def _scan_cross_mode_rp_safety(root: Path, checks: list[RPMatureQualityGateCheck], blockers: list[str], errors: list[str]) -> None:
    status = "pass"
    cross_root = root / "cross_mode"
    if cross_root.exists():
        for path in _iter_text_files(cross_root):
            rel = path.relative_to(root).as_posix() if root in path.parents else path.name
            text = _read_lower(path)
            if "tavern_to_world" in text and "rp_safety_metadata" not in text:
                blockers.append(f"tavern_world_missing_rp_safety_metadata:{redact_text(rel)}")
                status = "fail"
            if "tavern_to_world" in text and ("mature_only" in text or "contains_mature_content: true" in text or '"contains_mature_content": true' in text):
                blockers.append(f"mature_rp_to_world_blocked:{redact_text(rel)}")
                status = "fail"
            if "state_delta" in text or "gamestate" in text:
                errors.append(f"cross_mode_direct_world_mutation_risk:{redact_text(rel)}")
                status = "fail"
    checks.append(RPMatureQualityGateCheck(check_id="cross_mode_rp_safety_scan", status=status, message="Cross-mode Tavern/RP artifacts scanned for metadata, mature-to-world, and direct mutation blockers."))


def _scan_provider_policy(root: Path, checks: list[RPMatureQualityGateCheck], blockers: list[str]) -> None:
    status = "pass"
    provider_root = root / "providers"
    if provider_root.exists():
        for path in _iter_text_files(provider_root):
            rel = path.relative_to(root).as_posix() if root in path.parents else path.name
            text = _read_lower(path)
            if any(marker in text for marker in ("mature_fade_to_black", "explicit_adult_disabled_by_default", '"allow_mature_content": true', "allow_mature_content: true")):
                if '"allow_mature_content": true' not in text and "allow_mature_content: true" not in text:
                    blockers.append(f"provider_mature_rating_without_policy:{redact_text(rel)}")
                    status = "fail"
                if "log_prompts: true" in text or '"log_prompts": true' in text or "log_outputs: true" in text or '"log_outputs": true' in text:
                    blockers.append(f"provider_mature_logging_enabled:{redact_text(rel)}")
                    status = "fail"
    checks.append(RPMatureQualityGateCheck(check_id="provider_mature_policy_scan", status=status, message="Provider policies scanned for mature routing and sensitive logging blockers."))


def contains_forbidden_mature_policy_text(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in (
            '"can_access_hidden_facts": true',
            "can_access_hidden_facts: true",
            '"can_bypass_boundary": true',
            "can_bypass_boundary: true",
            '"can_bypass_provider_policy": true',
            "can_bypass_provider_policy: true",
            "default_enabled: true",
            '"default_enabled": true',
            '"api_key"',
            "authorization:",
            '"authorization"',
            "authorization",
            "sk-",
        )
    )
