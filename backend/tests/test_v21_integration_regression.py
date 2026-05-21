from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import GameState
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_migration import migrate_project_apply, migrate_project_dry_run
from app.platform.project_packages import export_project, import_project_apply, import_project_dry_run
from app.platform.project_repository import ProjectRepository
from app.platform.project_validation import validate_project
from app.platform.shared_libraries import (
    CharacterLibrary,
    CharacterProfile,
    CrossModeLink,
    CrossModeLinkRegistry,
    LoreFactEntry,
    LoreFactLibrary,
    ProjectMemoryLibrary,
    ProjectMemoryRecord,
    ProjectPromptProfile,
    ProjectProviderProfile,
    PromptProfileLibrary,
    ProviderProfileLibrary,
    TimelineEvent,
    TimelineLibrary,
    WorldBible,
    WorldBibleEntry,
    WorldBibleEntryType,
)
from app.quality.project_gate import run_project_quality_gate


def test_v21_project_core_api_mode_router_and_world_adapter_are_safe(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path / "projects")
    app.state.project_repository = repository
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, enable_debug_api=False, llm_provider="mock")
    if hasattr(app.state, "project_session_stores"):
        delattr(app.state, "project_session_stores")
    client = TestClient(app)

    created = client.post(
        "/projects",
        json={
            "project_id": "integration_project",
            "name": "Integration Project",
            "project_root": str(tmp_path / "projects" / "integration_project"),
        },
    )
    assert created.status_code == 200
    assert created.json()["project"]["project_id"] == "integration_project"

    listed = client.get("/projects")
    assert listed.status_code == 200
    assert listed.json()["projects"][0]["project_id"] == "integration_project"

    repository.update_project_metadata("integration_project", default_world_id="mist_valley")
    modes = client.get("/projects/integration_project/modes")
    assert modes.status_code == 200
    mode_payload = {item["mode"]: item for item in modes.json()["modes"]}
    assert mode_payload["novel"]["safe_summary"]["stub"] is True
    assert mode_payload["tavern"]["safe_summary"]["stub"] is True
    assert mode_payload["world"]["configured"] is True

    repository.create_project(
        NarrativeProject(
            project_id="missing_world_project",
            name="Missing World",
            project_root=str(tmp_path / "projects" / "missing_world_project"),
        )
    )
    missing = client.get("/projects/missing_world_project/modes/world")
    assert missing.status_code == 200
    assert missing.json()["configured"] is False
    assert "default_world_id not configured" in missing.json()["missing_requirements"]

    start = client.post("/projects/integration_project/world/start", json={"world_id": "mist_valley"})
    assert start.status_code == 200
    start_payload = start.json()
    assert start_payload["visible_state"]["world_id"] == "mist_valley"
    assert "hidden_facts" not in json.dumps(start_payload).lower()
    assert "api_key" not in json.dumps(start_payload).lower()

    stores = app.state.project_session_stores
    loop = next(store.get_session(start_payload["session_id"]) for store in stores.values())
    assert loop is not None
    result = loop.step("wait")
    assert result.event is not None
    assert loop.event_log.list_events()

    safe_response_text = json.dumps(client.get("/projects/integration_project/status").json()).lower()
    assert "api_key" not in safe_response_text
    assert "raw env" not in safe_response_text
    assert "hidden fact text" not in safe_response_text


def test_v21_shared_libraries_and_cross_mode_boundaries_do_not_mutate_state() -> None:
    state = GameState(world_id="mist_valley")
    before = state.model_dump(mode="json")

    characters = CharacterLibrary(project_id="integration")
    characters.add_character(
        CharacterProfile(
            character_id="mira",
            name="Mira",
            public_profile="Archivist",
            private_notes_authoring_only="hidden fact text for authoring only",
        )
    )
    assert "hidden fact text" not in json.dumps(characters.safe_summary()).lower()

    bible = WorldBible(world_bible_id="bible", project_id="integration", title="World Bible")
    bible.entries["safe"] = WorldBibleEntry(id="safe", title="Public Lore", content="safe lore")
    bible.entries["hidden"] = WorldBibleEntry(
        id="hidden",
        title="Hidden Lore",
        content="hidden fact text",
        entry_type=WorldBibleEntryType.HIDDEN,
        visibility="hidden",
    )
    assert "safe lore" in json.dumps(bible.safe_summary()).lower()
    assert "hidden fact text" not in json.dumps(bible.safe_summary()).lower()

    timeline = TimelineLibrary(project_id="integration")
    timeline.add_timeline_event(TimelineEvent(timeline_event_id="t2", project_id="integration", title="Hidden", description="hidden fact text", visibility="hidden"))
    timeline.add_timeline_event(TimelineEvent(timeline_event_id="t1", project_id="integration", title="Public", chronological_index=1))
    assert [item["timeline_event_id"] for item in timeline.safe_timeline_summary()] == ["t1"]

    lore = LoreFactLibrary(project_id="integration")
    lore.add_draft_lore(
        LoreFactEntry(
            id="flavor",
            project_id="integration",
            title="Flavor",
            text="narrator safe lore",
            fact_type="flavor",
            visibility="narrator_safe",
            safe_for_narrator=True,
            safe_for_tavern=True,
            safe_for_novel=True,
        )
    )
    lore.add_draft_lore(LoreFactEntry(id="hidden", project_id="integration", title="Hidden", text="hidden fact text", fact_type="hidden", visibility="hidden"))
    assert [item.id for item in lore.get_tavern_safe_lore()] == ["flavor"]
    assert lore.get_world_import_candidates() == []

    prompt_library = PromptProfileLibrary(
        project_id="integration",
        profiles={"safe": ProjectPromptProfile(profile_id="safe", mode_scopes=["novel", "tavern", "world"], narrator_style="concise")},
    )
    assert prompt_library.for_mode("world")[0].narrator_style == "concise"
    with pytest.raises(ValueError):
        ProjectPromptProfile(profile_id="unsafe", mode_scopes=["world"], can_access_hidden_facts=True)  # type: ignore[arg-type]

    provider_library = ProviderProfileLibrary(
        project_id="integration",
        profiles={
            "mock": ProjectProviderProfile(
                provider_profile_id="mock",
                provider_type="mock",
                display_name="Mock",
                api_key_env="LLM_API_KEY",
                allowed_modes=["world", "quality"],
            )
        },
    )
    assert provider_library.for_mode("world")[0].safe_export()["api_key_env"] == "LLM_API_KEY"
    with pytest.raises(ValueError):
        ProjectProviderProfile(provider_profile_id="bad", provider_type="mock", display_name="Bad", api_key="forbidden-placeholder")  # type: ignore[call-arg]

    memory = ProjectMemoryLibrary(
        project_id="integration",
        memories={
            "safe": ProjectMemoryRecord(memory_id="safe", project_id="integration", source_mode="world", content="safe memory", visibility="narrator_safe"),
            "hidden": ProjectMemoryRecord(memory_id="hidden", project_id="integration", source_mode="world", content="hidden fact text", visibility="hidden"),
        },
    )
    assert memory.memories["safe"].authoritative is False
    assert [item.memory_id for item in memory.get_memory_context_for_mode("world")] == ["safe"]

    links = CrossModeLinkRegistry(project_id="integration")
    links.create_link(
        CrossModeLink(
            link_id="valid",
            project_id="integration",
            source_mode="novel",
            source_ref="novel:scene:1",
            target_mode="world",
            target_ref="world:event:1",
            link_type="world_event_to_novel_scene",
        )
    )
    assert links.validate_link("valid", {"novel:scene:1", "world:event:1"}).ok
    links.create_link(
        CrossModeLink(
            link_id="hidden",
            project_id="integration",
            source_mode="world",
            source_ref="world:fact:hidden",
            target_mode="novel",
            target_ref="novel:outline:1",
            link_type="world_fact_to_world_bible_entry",
            hidden=True,
            notes="hidden fact text",
        )
    )
    assert links.links["hidden"].safe_summary() is None
    broken = links.create_link(
        CrossModeLink(
            link_id="broken",
            project_id="integration",
            source_mode="tavern",
            source_ref="missing",
            target_mode="world",
            target_ref="also_missing",
            link_type="rp_session_to_memory",
        )
    )
    assert links.validate_link(broken.link_id, {"known"}).ok is False
    assert links.links["broken"].status == "broken"
    assert state.model_dump(mode="json") == before


def test_v21_project_import_export_migration_validation_and_quality_gate_regressions(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path / "projects")
    project = repository.create_project(
        NarrativeProject(project_id="portable_project", name="Portable", project_root=str(tmp_path / "projects" / "portable_project"))
    )
    project_root = Path(project.project_root)
    (project_root / ".env").write_text("OPENAI_API_KEY=not-a-real-test-value", encoding="utf-8")
    (project_root / "providers" / "profiles" / "provider.json").write_text(
        json.dumps({"provider_profile_id": "mock", "provider_type": "mock", "display_name": "Mock", "api_key_env": "LLM_API_KEY"}),
        encoding="utf-8",
    )

    exported = export_project("portable_project", repository)
    with ZipFile(BytesIO(base64.b64decode(exported.archive_base64))) as archive:
        names = archive.namelist()
        text_payload = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in names
            if name.endswith((".json", ".yaml", ".yml", ".md", ".txt"))
        ).lower()
    assert ".env" not in names
    assert "openai_api_key" not in text_payload
    assert "not-a-real-test-value" not in text_payload

    target_root = tmp_path / "imports"
    dry_run = import_project_dry_run(exported.archive_base64, target_root, repository)
    assert dry_run.ok
    assert not (target_root / "portable_project").exists()
    applied = import_project_apply(exported.archive_base64, target_root, repository, confirm_apply=True)
    assert applied.imported
    duplicate = import_project_dry_run(exported.archive_base64, target_root, repository)
    assert not duplicate.ok
    assert any("duplicate project_id" in error for error in duplicate.errors)
    assert not import_project_dry_run(_zip_slip_archive(), tmp_path / "slip", repository).ok

    assert not validate_project(project_root).ok
    (project_root / ".env").unlink()
    assert validate_project(project_root).ok

    (project_root / "cross_mode_links.json").write_text(
        json.dumps({"links": [{"link_id": "bad", "source_ref": "novel:1", "target_ref": "", "status": "broken"}]}),
        encoding="utf-8",
    )
    broken_report = validate_project(project_root)
    assert not broken_report.ok
    assert {issue.code for issue in broken_report.errors} >= {"cross_mode_link_broken", "cross_mode_link_invalid_ref"}
    gate = run_project_quality_gate(project_root)
    assert not gate.passed
    assert gate.blockers

    old_root = tmp_path / "v20"
    (old_root / "worlds" / "mist_valley").mkdir(parents=True)
    (old_root / "worlds" / "mist_valley" / "manifest.yaml").write_text("world_id: mist_valley\nname: Mist Valley\n", encoding="utf-8")
    (old_root / "saves").mkdir()
    (old_root / "saves" / "save.json").write_text("{}", encoding="utf-8")
    (old_root / ".env").write_text("OPENAI_API_KEY=not-a-real-test-value", encoding="utf-8")
    original_listing = sorted(path.relative_to(old_root).as_posix() for path in old_root.rglob("*"))
    migration_dry_run = migrate_project_dry_run(old_root, tmp_path / "migrated", project_id="migrated_project")
    assert migration_dry_run.plan.can_migrate
    assert not (tmp_path / "migrated").exists()
    migration_apply = migrate_project_apply(old_root, tmp_path / "migrated", ProjectRepository(tmp_path), confirm_apply=True, project_id="migrated_project")
    assert migration_apply.applied
    assert (tmp_path / "migrated" / "project.yaml").exists()
    assert not (tmp_path / "migrated" / ".env").exists()
    assert original_listing == sorted(path.relative_to(old_root).as_posix() for path in old_root.rglob("*"))


def test_v21_frontend_project_shell_static_contract() -> None:
    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = Path("frontend/src/api.ts").read_text(encoding="utf-8")
    assert "ProjectShell" in app_source
    assert "Novel Studio MVP coming in v2.2" in app_source
    assert "Tavern Studio MVP coming in v2.3" in app_source
    assert "No API keys, hidden facts, or raw env" in app_source
    assert "fetchNarrativeProjects" in api_source
    assert "createNarrativeProject" in api_source
    project_shell_slice = app_source[app_source.index("function ProjectShell") : app_source.index("function ProjectModeCard")]
    assert "sk-" not in project_shell_slice
    assert "apiKey" not in project_shell_slice
    assert "hidden fact text" not in project_shell_slice.lower()


def _zip_slip_archive() -> str:
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        archive.writestr("project_package_manifest.json", "{}")
        archive.writestr("../evil.txt", "evil")
    return base64.b64encode(out.getvalue()).decode("ascii")
