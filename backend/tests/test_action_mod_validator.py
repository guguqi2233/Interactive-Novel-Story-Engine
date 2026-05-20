from pathlib import Path

from app.core.state_delta import StateDeltaOperation
from app.engine.action_mod_validator import validate_action_mods
from app.engine.actions.declarative import (
    DeclarativeActionDefinition,
    DeclarativeActionTargetSpec,
    DeclarativeOutcome,
    DeclarativeStateDeltaTemplate,
    DeclarativeTargetKind,
    DeclarativeVisibilityPolicy,
)
from app.engine.gameplay_module_loader import (
    GameplayModuleLoader,
    GameplayModuleManifest,
    GameplayModulePermissions,
)
from app.engine.actions.schemas import SuccessLevel
from app.quality.gameplay_module_quality import run_action_mod_quality_gate


def _action(
    action_id: str = "magic.pray",
    *,
    aliases: list[str] | None = None,
    path: str = "flags.prayed",
    hidden_outcome: bool = False,
    hidden_visible_policy: bool = False,
    target_specs: list[DeclarativeActionTargetSpec] | None = None,
    visible_facts: list[str] | None = None,
    hidden_facts: list[str] | None = None,
) -> DeclarativeActionDefinition:
    return DeclarativeActionDefinition(
        id=action_id,
        label="Pray",
        aliases=aliases or ["pray"],
        category="general",
        target_specs=target_specs
        if target_specs is not None
        else [DeclarativeActionTargetSpec(kind=DeclarativeTargetKind.CURRENT_LOCATION)],
        outcomes={
            SuccessLevel.SUCCESS: DeclarativeOutcome(
                success_level=SuccessLevel.SUCCESS,
                reason="The action is resolved by deterministic module rules.",
                visible_facts=visible_facts or [],
                hidden_facts=hidden_facts or [],
                hidden_outcome=hidden_outcome,
                state_delta_templates=[
                    DeclarativeStateDeltaTemplate(
                        operation=StateDeltaOperation.SET,
                        path=path,
                        value=True,
                    )
                ],
            )
        },
        event_type=f"{action_id}.resolved",
        visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=hidden_visible_policy),
    )


def _manifest(*, execute_code: bool = False) -> GameplayModuleManifest:
    return GameplayModuleManifest(
        id="magic_basics",
        name="Magic Basics",
        version="0.1.0",
        module_type="action_pack",
        engine_version_min="0.1.0",
        provided_actions=[{"id": "magic.pray", "action_type": "magic.pray"}],
        permissions=GameplayModulePermissions(execute_code=execute_code),
    )


def test_valid_action_mod_passes() -> None:
    report = validate_action_mods([_action()], module_id="magic_basics", manifest=_manifest())

    assert report.ok
    assert report.errors == []


def test_alias_conflict_is_reported_as_warning() -> None:
    report = validate_action_mods(
        [
            _action("magic.pray", aliases=["invoke"]),
            _action("magic.invoke", aliases=["invoke"]),
        ],
        module_id="magic_basics",
    )

    assert report.ok
    assert any(issue.code == "action_mod_alias_conflict" for issue in report.warnings)


def test_forbidden_state_delta_path_is_error() -> None:
    report = validate_action_mods([_action(path="player.hp")], module_id="magic_basics")

    assert not report.ok
    assert any(issue.code == "action_mod_forbidden_state_delta_path" for issue in report.errors)


def test_execute_code_permission_is_rejected() -> None:
    report = validate_action_mods([_action()], module_id="magic_basics", manifest=_manifest(execute_code=True))

    assert not report.ok
    assert any(issue.code == "action_mod_execute_code_forbidden" for issue in report.errors)


def test_hidden_output_policy_error_is_caught() -> None:
    report = validate_action_mods(
        [
            _action(
                hidden_outcome=True,
                hidden_visible_policy=True,
                visible_facts=["secret_oath"],
                hidden_facts=["secret_oath"],
            )
        ],
        module_id="magic_basics",
    )

    codes = {issue.code for issue in report.errors}
    assert "action_mod_hidden_outcome_visible_policy" in codes
    assert "action_mod_hidden_output_visible" in codes


def test_invalid_target_spec_is_caught() -> None:
    report = validate_action_mods(
        [
            _action(
                target_specs=[
                    DeclarativeActionTargetSpec(
                        kind=DeclarativeTargetKind.SELF,
                        allowed_ids=["player"],
                    )
                ]
            )
        ],
        module_id="magic_basics",
    )

    assert not report.ok
    assert any(issue.code == "action_mod_invalid_target_spec" for issue in report.errors)


def test_module_validation_runs_action_mod_validator(tmp_path: Path) -> None:
    module_path = tmp_path / "gameplay_modules" / "magic_basics"
    module_path.joinpath("action_mods").mkdir(parents=True)
    module_path.joinpath("gameplay_module.yaml").write_text(
        """
id: magic_basics
name: Magic Basics
version: 0.1.0
module_type: action_pack
engine_version_min: 0.1.0
schema_version: "0.6"
provided_actions:
  - id: magic.pray
    action_type: magic.pray
permissions:
  execute_code: false
save_compatibility:
  safe_to_add_mid_save: true
  migration_required: false
  requires_new_game: false
  migration_defaults: {}
""",
        encoding="utf-8",
    )
    module_path.joinpath("action_mods", "actions.yaml").write_text(
        """
actions:
  - id: magic.pray
    label: Pray
    aliases: [pray]
    category: general
    outcomes:
      success:
        success_level: success
        reason: Safe action.
        state_delta_templates:
          - operation: set
            path: player.hp
            value: 3
    event_type: magic.pray.resolved
""",
        encoding="utf-8",
    )

    report = GameplayModuleLoader(tmp_path / "gameplay_modules").validate_module("magic_basics")

    assert not report.ok
    assert any(issue.code == "action_mod_forbidden_state_delta_path" for issue in report.errors)


def test_quality_gate_can_call_action_mod_validator() -> None:
    report = run_action_mod_quality_gate([_action(path="player.hp")], module_id="magic_basics")

    assert report.summary["ok"] is False
    assert any(issue.category == "gameplay_module_action_mod" for issue in report.issues)
