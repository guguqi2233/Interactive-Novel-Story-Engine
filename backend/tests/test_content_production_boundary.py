from pathlib import Path

from app.core.world_state import GameState, LocationState
from app.engine.content.content_production_boundary import (
    ContentProductionCheckRequest,
    ContentProductionDecision,
    ContentProductionDraft,
    ContentProductionOperation,
    check_content_production_boundary,
    default_content_production_policy,
)


def test_content_production_policy_marks_preview_read_only(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    result = check_content_production_boundary(
        ContentProductionCheckRequest(operation=ContentProductionOperation.PREVIEW)
    )

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert result.writes_disk is False
    assert result.modifies_active_game_state is False
    assert result.decision == ContentProductionDecision.ALLOW
    assert after == before


def test_content_production_policy_marks_validate_read_only(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    result = check_content_production_boundary(
        ContentProductionCheckRequest(operation=ContentProductionOperation.VALIDATE)
    )

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert result.writes_disk is False
    assert result.modifies_active_game_state is False
    assert result.decision == ContentProductionDecision.ALLOW
    assert after == before


def test_generated_draft_does_not_modify_active_game_state() -> None:
    state = GameState(
        world_id="production-boundary-test",
        locations={"square": LocationState(id="square", name="Square")},
    )
    before = state.model_dump(mode="json")

    draft = ContentProductionDraft(
        id="npc-pack-draft",
        draft_type="npc_pack",
        content={"npc_id": "mira"},
    )
    result = check_content_production_boundary(
        ContentProductionCheckRequest(operation=ContentProductionOperation.GENERATE)
    )

    assert draft.content["npc_id"] == "mira"
    assert result.decision == ContentProductionDecision.ALLOW
    assert state.model_dump(mode="json") == before


def test_apply_requires_validation_gate() -> None:
    result = check_content_production_boundary(
        ContentProductionCheckRequest(
            operation=ContentProductionOperation.APPLY,
            explicit_apply=True,
        )
    )

    assert result.requires_validation_gate is True
    assert result.decision == ContentProductionDecision.BLOCK_VALIDATION_GATE


def test_batch_apply_requires_dry_run_before_validation_gate() -> None:
    result = check_content_production_boundary(
        ContentProductionCheckRequest(
            operation=ContentProductionOperation.BATCH_APPLY,
            explicit_apply=True,
            validation_gate_passed=True,
        )
    )

    assert result.requires_dry_run is True
    assert result.decision == ContentProductionDecision.BLOCK_MISSING_DRY_RUN


def test_hidden_content_does_not_enter_normal_production_report() -> None:
    secret = "The culprit buried the knife under the chapel floor."
    draft = ContentProductionDraft(
        id="mystery-case",
        draft_type="mystery",
        content={"public_hook": "A bell rings at midnight."},
        hidden_content={"culprit_truth": secret},
    )

    report = draft.normal_report()
    serialized = report.model_dump_json()

    assert report.hidden_item_count == 1
    assert "culprit_truth" in serialized
    assert secret not in serialized


def test_policy_blocks_script_execution() -> None:
    result = check_content_production_boundary(
        ContentProductionCheckRequest(
            operation=ContentProductionOperation.BUILD_PACKAGE,
            explicit_apply=True,
            validation_gate_passed=True,
            quality_gate_passed=True,
            executes_script=True,
        )
    )

    assert result.decision == ContentProductionDecision.BLOCK_SCRIPT_EXECUTION
    assert default_content_production_policy().package_executes_scripts is False
