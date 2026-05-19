from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db.repository import SQLiteSaveRepository  # noqa: E402
from app.engine.content.authoring_service import ContentAuthoringService  # noqa: E402
from app.engine.content.campaign_starter_kit import (  # noqa: E402
    CampaignStarterKitBuildRequest,
    CampaignStarterKitDraft,
    build_campaign_starter_kit,
    preview_campaign_starter_kit,
)
from app.engine.content.content_batch_validator import (  # noqa: E402
    BatchPackageType,
    ContentBatchValidationRequest,
    ContentBatchValidationTarget,
    validate_content_batch,
)
from app.engine.content.npc_pack_generator import (  # noqa: E402
    NPCPackGeneratorApplyRequest,
    NPCPackGeneratorDraft,
    apply_npc_pack_generator,
    preview_npc_pack_generator,
    validate_npc_pack_generator,
)
from app.engine.content.quest_pack_generator import (  # noqa: E402
    QuestPackGeneratorApplyRequest,
    QuestPackGeneratorDraft,
    apply_quest_pack_generator,
    preview_quest_pack_generator,
    validate_quest_pack_generator,
)
from app.engine.content.script_package_builder import (  # noqa: E402
    ScriptPackageBuildRequest,
    ScriptPackageFile,
    ScriptPackageManifest,
    build_script_package,
    build_script_package_dry_run,
    validate_script_package,
)
from app.engine.content.world_pack_wizard import (  # noqa: E402
    WorldPackWizard,
    WorldPackWizardApplyRequest,
    WorldPackWizardDraft,
)
from app.quality.batch_quality_gate import BatchQualityGateRequest, BatchQualityGateThresholds, run_batch_quality_gate  # noqa: E402
from app.quality.content_coverage_planner import ContentCoveragePlanRequest, build_content_coverage_plan  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local content production pipeline CLI.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--worlds-root", default="worlds")
    parser.add_argument("--packages-root", default="packages")
    parser.add_argument("--database-url", default="sqlite:///./world_engine_cli.db")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _world_wizard_parser(subparsers)
    _npc_pack_parser(subparsers)
    _quest_pack_parser(subparsers)
    _batch_validate_parser(subparsers)
    _script_package_parser(subparsers)
    _campaign_starter_parser(subparsers)
    _coverage_plan_parser(subparsers)
    _batch_quality_gate_parser(subparsers)

    args = parser.parse_args(argv)
    try:
        result, ok = _dispatch(args)
    except Exception as exc:
        message = _redact(str(exc))
        if args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2))
        else:
            print(f"ERROR: {message}", file=sys.stderr)
        return 2
    _print_result(result, json_mode=args.json)
    return 0 if ok else 1


def _world_wizard_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("world-wizard", help="Preview/validate/apply a world pack wizard draft.")
    parser.add_argument("--world-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--genre", default="fantasy")
    parser.add_argument("--tone", default="grounded")
    parser.add_argument("--starting-location", default="start")
    parser.add_argument("--locations", type=int, default=3)
    parser.add_argument("--npcs", type=int, default=2)
    parser.add_argument("--quests", type=int, default=1)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--apply", action="store_true")


def _npc_pack_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("npc-pack", help="Preview/validate/apply an NPC pack draft.")
    parser.add_argument("--world-id", required=True)
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--theme", default="local cast")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--factions", default="")
    parser.add_argument("--locations", default="")
    parser.add_argument("--archetypes", default="guide,witness,merchant")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--apply", action="store_true")


def _quest_pack_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("quest-pack", help="Preview/validate/apply a quest pack draft.")
    parser.add_argument("--world-id", required=True)
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--theme", default="starter quest")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--npcs", default="")
    parser.add_argument("--locations", default="")
    parser.add_argument("--factions", default="")
    parser.add_argument("--facts", default="")
    parser.add_argument("--mystery", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--apply", action="store_true")


def _batch_validate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("batch-validate", help="Batch validate local content targets.")
    parser.add_argument("--packages-root", default="packages")
    parser.add_argument("--templates-root", default="templates")
    parser.add_argument("--mods-root", default="mods")
    parser.add_argument("--target", action="append", default=[])


def _script_package_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("build-script-package", help="Dry-run/validate/build a non-executable script package.")
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--worlds", default="")
    parser.add_argument("--quests", default="")
    parser.add_argument("--characters", default="")
    parser.add_argument("--templates", default="")
    parser.add_argument("--scenarios", default="")
    parser.add_argument("--dependencies", default="")
    parser.add_argument("--conflicts", default="")
    parser.add_argument("--file", action="append", default=[], help="Data file path=content.")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--apply", action="store_true")


def _campaign_starter_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("campaign-starter", help="Preview/build a campaign starter kit draft.")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--genre", default="mystery")
    parser.add_argument("--tone", default="grounded")
    parser.add_argument("--starting-region", default="start")
    parser.add_argument("--core-conflict", default="local mystery")
    parser.add_argument("--npcs", type=int, default=3)
    parser.add_argument("--questlines", type=int, default=1)
    parser.add_argument("--factions", type=int, default=2)
    parser.add_argument("--no-mystery", action="store_true")
    parser.add_argument("--playtime", type=int, default=2)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--apply", action="store_true")


def _coverage_plan_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("coverage-plan", help="Generate a safe content coverage plan.")
    parser.add_argument("--world-id", required=True)
    parser.add_argument("--genre", default="general")
    parser.add_argument("--playtime", default="short")
    parser.add_argument("--complexity", default="medium")


def _batch_quality_gate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("batch-quality-gate", help="Run a redacted batch quality gate for worlds and packages.")
    parser.add_argument("--world", action="append", default=[])
    parser.add_argument("--package", action="append", default=[])
    parser.add_argument("--package-type", default=BatchPackageType.SCRIPT_PACKAGE.value, choices=[item.value for item in BatchPackageType])
    parser.add_argument("--profile", default="fast", choices=["fast", "standard", "strict"])
    parser.add_argument("--max-warnings", type=int, default=999)
    parser.add_argument("--min-health-score", type=int, default=0)
    parser.add_argument("--include-playtests", action="store_true")


def _dispatch(args: argparse.Namespace) -> tuple[Any, bool]:
    if args.command == "world-wizard":
        return _run_world_wizard(args)
    if args.command == "npc-pack":
        return _run_npc_pack(args)
    if args.command == "quest-pack":
        return _run_quest_pack(args)
    if args.command == "batch-validate":
        return _run_batch_validate(args)
    if args.command == "build-script-package":
        return _run_script_package(args)
    if args.command == "campaign-starter":
        return _run_campaign_starter(args)
    if args.command == "coverage-plan":
        return _run_coverage_plan(args)
    if args.command == "batch-quality-gate":
        return _run_batch_quality_gate(args)
    raise ValueError(f"Unknown command: {args.command}")


def _run_world_wizard(args: argparse.Namespace) -> tuple[Any, bool]:
    draft = WorldPackWizardDraft(
        world_id=args.world_id,
        name=args.name,
        genre=args.genre,
        tone=args.tone,
        starting_location=args.starting_location,
        location_seed_count=args.locations,
        npc_seed_count=args.npcs,
        quest_seed_count=args.quests,
        enabled_systems=["quests", "roleplay", "npc_simulation", "factions", "rumors"],
    )
    wizard = WorldPackWizard(args.worlds_root)
    if args.apply:
        result = wizard.apply_to_worlds_directory(WorldPackWizardApplyRequest(draft=draft, confirm_apply=True, confirm_warnings=True))
    elif args.validate:
        result = wizard.validate_draft(draft)
    else:
        result = wizard.preview_files(draft)
    return result, _validation_ok(result)


def _run_npc_pack(args: argparse.Namespace) -> tuple[Any, bool]:
    draft = NPCPackGeneratorDraft(
        target_world_id=args.world_id,
        pack_id=args.pack_id,
        theme=args.theme,
        npc_count=args.count,
        faction_ids=_csv(args.factions),
        location_ids=_csv(args.locations),
        archetypes=_csv(args.archetypes),
        rp_style="medium",
    )
    service = ContentAuthoringService(args.worlds_root)
    if args.apply:
        result = apply_npc_pack_generator(NPCPackGeneratorApplyRequest(draft=draft, confirm_apply=True, confirm_warnings=True), service)
    elif args.validate:
        result = validate_npc_pack_generator(draft, service)
    else:
        result = preview_npc_pack_generator(draft, service)
    return result, _validation_ok(result)


def _run_quest_pack(args: argparse.Namespace) -> tuple[Any, bool]:
    draft = QuestPackGeneratorDraft(
        target_world_id=args.world_id,
        pack_id=args.pack_id,
        theme=args.theme,
        quest_count=args.count,
        involved_npcs=_csv(args.npcs),
        involved_locations=_csv(args.locations),
        involved_factions=_csv(args.factions),
        required_facts=_csv(args.facts),
        mystery_mode=args.mystery,
        failure_paths_enabled=True,
    )
    service = ContentAuthoringService(args.worlds_root)
    if args.apply:
        result = apply_quest_pack_generator(QuestPackGeneratorApplyRequest(draft=draft, confirm_apply=True, confirm_warnings=True), service)
    elif args.validate:
        result = validate_quest_pack_generator(draft, service)
    else:
        result = preview_quest_pack_generator(draft, service)
    return result, _validation_ok(result)


def _run_batch_validate(args: argparse.Namespace) -> tuple[Any, bool]:
    request = ContentBatchValidationRequest(
        targets=[_parse_target(value) for value in args.target],
        worlds_root=args.worlds_root,
        packages_root=args.packages_root,
        templates_root=args.templates_root,
        mods_root=args.mods_root,
    )
    result = validate_content_batch(request)
    return result, result.failed == 0


def _run_script_package(args: argparse.Namespace) -> tuple[Any, bool]:
    request = ScriptPackageBuildRequest(
        manifest=ScriptPackageManifest(
            package_id=args.package_id,
            name=args.name,
            included_worlds=_csv(args.worlds),
            included_quests=_csv(args.quests),
            included_characters=_csv(args.characters),
            included_templates=_csv(args.templates),
            included_scenarios=_csv(args.scenarios),
            dependencies=_csv(args.dependencies),
            conflicts=_csv(args.conflicts),
        ),
        files=[_parse_script_file(value) for value in args.file],
        available_dependency_ids=_csv(args.dependencies) + _csv(args.worlds),
        packages_root=args.packages_root,
        confirm_apply=args.apply,
    )
    if args.apply:
        result = build_script_package(request)
    elif args.validate:
        result = validate_script_package(request)
    else:
        result = build_script_package_dry_run(request)
    return result, _validation_ok(result)


def _run_campaign_starter(args: argparse.Namespace) -> tuple[Any, bool]:
    draft = CampaignStarterKitDraft(
        campaign_id=args.campaign_id,
        name=args.name,
        genre=args.genre,
        tone=args.tone,
        starting_region=args.starting_region,
        core_conflict=args.core_conflict,
        npc_count=args.npcs,
        questline_count=args.questlines,
        faction_count=args.factions,
        mystery_enabled=not args.no_mystery,
        target_playtime_hours=args.playtime,
    )
    if args.apply:
        result = build_campaign_starter_kit(CampaignStarterKitBuildRequest(draft=draft, confirm_build=True), worlds_root=args.worlds_root)
    else:
        result = preview_campaign_starter_kit(draft, worlds_root=args.worlds_root)
    return result, _validation_ok(result)


def _run_coverage_plan(args: argparse.Namespace) -> tuple[Any, bool]:
    result = build_content_coverage_plan(
        ContentCoveragePlanRequest(
            target_world=args.world_id,
            genre=args.genre,
            desired_playtime=args.playtime,
            desired_complexity=args.complexity,
        ),
        worlds_root=args.worlds_root,
    )
    return result, True


def _run_batch_quality_gate(args: argparse.Namespace) -> tuple[Any, bool]:
    result = run_batch_quality_gate(
        BatchQualityGateRequest(
            world_ids=args.world,
            package_ids=args.package,
            package_type=BatchPackageType(args.package_type),
            profile=args.profile,
            thresholds=BatchQualityGateThresholds(max_warnings=args.max_warnings, min_health_score=args.min_health_score),
            include_playtests=args.include_playtests,
            worlds_root=args.worlds_root,
            packages_root=args.packages_root,
        )
    )
    return result, result.passed


def _parse_target(value: str) -> ContentBatchValidationTarget:
    parts = value.split(":", 2)
    if len(parts) < 2:
        raise ValueError("--target must be type:id or type:id:path")
    return ContentBatchValidationTarget(package_type=BatchPackageType(parts[0]), id=parts[1], path=parts[2] if len(parts) == 3 else None)


def _parse_script_file(value: str) -> ScriptPackageFile:
    if "=" not in value:
        raise ValueError("--file must be path=content")
    path, content = value.split("=", 1)
    return ScriptPackageFile(path=path, content=content)


def _print_result(result: Any, *, json_mode: bool) -> None:
    payload = _redacted_model_dump(result)
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(_human_summary(payload))


def _redacted_model_dump(result: Any) -> Any:
    if hasattr(result, "model_dump"):
        payload = result.model_dump(mode="json")
    else:
        payload = result
    return _redact_value(payload)


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact(value)
    if isinstance(value, dict):
        return {str(key): _redact_value(child) for key, child in value.items() if str(key).lower() not in {"archive_base64"}}
    if isinstance(value, list):
        return [_redact_value(child) for child in value]
    return value


def _redact(value: str) -> str:
    result = value
    for token in ("sk-", "api_key", "apikey", ".env", "secret", "hidden", "private_self_summary", "sealed_letter_under_stone"):
        result = result.replace(token, "[redacted]")
        result = result.replace(token.upper(), "[redacted]")
    return result


def _human_summary(payload: Any) -> str:
    if not isinstance(payload, dict):
        return str(payload)
    validation = payload.get("validation")
    ok = validation.get("ok") if isinstance(validation, dict) else payload.get("ok", True)
    lines = [f"ok={ok}"]
    for key in ("writes_to_disk", "applied", "built", "dry_run"):
        if key in payload:
            lines.append(f"{key}={payload[key]}")
    if "total" in payload:
        lines.append(f"total={payload.get('total')} passed={payload.get('passed')} warning={payload.get('warning')} failed={payload.get('failed')}")
    if "draft" in payload and isinstance(payload["draft"], dict):
        lines.append(f"draft={payload['draft'].get('campaign_id') or payload['draft'].get('world_id') or payload['draft'].get('pack_id')}")
    if "manifest" in payload and isinstance(payload["manifest"], dict):
        lines.append(f"package={payload['manifest'].get('package_id')}")
    if "passed" in payload and "aggregate_summary" in payload:
        lines.append(f"passed={payload.get('passed')}")
        summary = payload.get("aggregate_summary") or {}
        if isinstance(summary, dict):
            lines.append(f"total={summary.get('total')} failed={summary.get('failed')}")
    return "\n".join(lines)


def _validation_ok(result: Any) -> bool:
    validation = getattr(result, "validation", None)
    if validation is None:
        return bool(getattr(result, "ok", True))
    return bool(getattr(validation, "ok", False))


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
