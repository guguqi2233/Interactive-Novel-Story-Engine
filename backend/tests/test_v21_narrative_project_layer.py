from __future__ import annotations

import base64
import json
import subprocess
import sys
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
from app.platform.project_modes import (
    ChapterDraft,
    NovelModeProjectState,
    RPProposalDraft,
    TavernSessionDraft,
    WorldProjectSection,
)
from app.platform.project_packages import export_project, import_project_apply, import_project_dry_run
from app.platform.project_repository import ProjectRepository
from app.platform.project_validation import validate_project
from app.platform.project_workspace import create_project_workspace
from app.platform.shared_libraries import (
    CharacterLibrary,
    CharacterProfile,
    CrossModeLink,
    CrossModeLinkRegistry,
    ProjectMemoryLibrary,
    ProjectMemoryRecord,
    ProjectProviderProfile,
    ProviderProfileLibrary,
    WorldBible,
    WorldBibleEntry,
    WorldBibleEntryType,
)
from app.quality.project_gate import run_project_quality_gate


def test_v21_narrative_project_schema_workspace_repository_and_libraries(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    repository = ProjectRepository(root)
    project = NarrativeProject(project_id="demo_project", name="Demo", project_root=str(root / "demo_project"))
    created = repository.create_project(project)

    assert created.schema_version
    assert (Path(created.project_root) / "project.yaml").exists()
    assert (Path(created.project_root) / "novel" / "drafts").exists()

    loaded = repository.load_project("demo_project")
    assert loaded.project_id == "demo_project"
    assert repository.list_projects()[0].project_id == "demo_project"

    characters = CharacterLibrary(project_id="demo_project")
    characters.add_character(CharacterProfile(character_id="harlan", name="Harlan", private_notes_authoring_only="secret"))
    assert "private_notes" not in json.dumps(characters.safe_summary()).lower()

    bible = WorldBible(world_bible_id="bible", project_id="demo_project", title="Bible")
    bible.entries["public"] = WorldBibleEntry(id="public", title="Public", content="Safe lore")
    bible.entries["hidden"] = WorldBibleEntry(id="hidden", title="Hidden", content="hidden fact text", entry_type=WorldBibleEntryType.HIDDEN, visibility="hidden")
    assert "hidden fact text" not in json.dumps(bible.safe_summary()).lower()

    memory = ProjectMemoryLibrary(project_id="demo_project")
    memory.memories["m1"] = ProjectMemoryRecord(memory_id="m1", project_id="demo_project", source_mode="tavern", content="safe", visibility="tavern_safe")
    memory.memories["m2"] = ProjectMemoryRecord(memory_id="m2", project_id="demo_project", source_mode="world", content="hidden", visibility="hidden")
    assert [item.memory_id for item in memory.get_memory_context_for_mode("tavern")] == ["m1"]


def test_v21_prompt_provider_links_and_mode_stubs_do_not_modify_gamestate() -> None:
    state = GameState(world_id="before")
    before = state.model_dump(mode="json")

    provider = ProjectProviderProfile(
        provider_profile_id="mock_profile",
        provider_type="mock",
        display_name="Mock",
        api_key_env="LLM_API_KEY",
        allowed_modes=["novel", "tavern", "world"],
    )
    library = ProviderProfileLibrary(project_id="demo", profiles={provider.provider_profile_id: provider})
    assert library.for_mode("world")[0].safe_export()["api_key_env"] == "LLM_API_KEY"
    with pytest.raises(ValueError):
        ProjectProviderProfile(provider_profile_id="bad", provider_type="mock", display_name="Bad", api_key="sk-real-looking-secret-1234567890")  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        ProjectProviderProfile(
            provider_profile_id="bad_env",
            provider_type="mock",
            display_name="Bad Env",
            api_key_env="sk-real-looking-secret-1234567890",
        )

    chapter = ChapterDraft(chapter_id="c1", project_id="demo", title="Chapter", content="draft only")
    novel = NovelModeProjectState(project_id="demo", chapters={"c1": chapter})
    tavern = TavernSessionDraft(
        session_id="s1",
        project_id="demo",
        title="Session",
        proposals=[RPProposalDraft(proposal_id="p1", proposal_type="new_fact", summary="draft fact")],
    )
    assert novel.safe_summary()["chapters_count"] == 1
    assert tavern.proposals[0].creates_world_fact is False
    assert state.model_dump(mode="json") == before


def test_v21_cross_mode_link_project_package_migration_validation_and_gate(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path)
    project_root = tmp_path / "demo"
    project = repository.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    (project_root / "novel" / "drafts" / "chapter.md").write_text("safe draft", encoding="utf-8")

    registry = CrossModeLinkRegistry(project_id="demo")
    registry.create_link(CrossModeLink(link_id="link1", project_id="demo", source_mode="novel", source_ref="chapter:c1", target_mode="world", target_ref="npc:harlan", link_type="novel_character_to_character_profile"))
    assert registry.validate_link("link1", {"chapter:c1"}).ok is False
    assert registry.links["link1"].status == "broken"

    exported = export_project("demo", repository)
    assert ".env" not in exported.archive_base64.lower()
    dry_run = import_project_dry_run(exported.archive_base64, tmp_path / "imports", repository)
    assert dry_run.ok
    applied = import_project_apply(exported.archive_base64, tmp_path / "imports", repository, confirm_apply=True)
    assert applied.imported

    tampered = _tamper_checksum(exported.archive_base64)
    assert not import_project_dry_run(tampered, tmp_path / "x", repository).ok
    assert not import_project_dry_run(_zip_slip_archive(), tmp_path / "x", repository).ok
    assert not import_project_dry_run(_executable_archive(), tmp_path / "x", repository).ok

    report = validate_project(project.project_root)
    assert report.ok
    gate = run_project_quality_gate(project.project_root)
    assert gate.passed

    old = tmp_path / "old"
    (old / "worlds" / "demo_world").mkdir(parents=True)
    (old / "worlds" / "demo_world" / "manifest.yaml").write_text("world_id: demo_world\nname: Demo\n", encoding="utf-8")
    (old / ".env").write_text("LLM_API_KEY=sk-real-looking-secret-1234567890", encoding="utf-8")
    migration = migrate_project_dry_run(old, tmp_path / "migrated", project_id="migrated")
    assert migration.plan.can_migrate
    assert not (tmp_path / "migrated").exists()
    applied_migration = migrate_project_apply(old, tmp_path / "migrated", ProjectRepository(tmp_path), confirm_apply=True, project_id="migrated")
    assert applied_migration.applied
    assert applied_migration.migration_history
    assert not (tmp_path / "migrated" / ".env").exists()


def test_v21_project_validation_resolves_cross_mode_link_refs(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path)
    project = repository.create_project(NarrativeProject(project_id="links", name="Links", project_root=str(tmp_path / "links")))
    project_root = Path(project.project_root)
    (project_root / "novel" / "drafts" / "chapter.md").write_text("safe draft", encoding="utf-8")
    (project_root / "world" / "content_pack" / "npc.yaml").write_text("id: npc\n", encoding="utf-8")
    (project_root / "cross_mode_links.json").write_text(
        json.dumps(
            {
                "links": [
                    {
                        "link_id": "valid",
                        "source_ref": "novel:drafts/chapter",
                        "target_ref": "world:content_pack/npc",
                    },
                    {
                        "link_id": "missing",
                        "source_ref": "novel:missing",
                        "target_ref": "world:content_pack/npc",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    report = validate_project(project_root)
    assert not report.ok
    codes = {issue.code for issue in report.errors}
    assert "cross_mode_link_source_missing" in codes
    assert "cross_mode_link_target_missing" not in codes


def test_v21_project_api_and_world_adapter(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path / "projects")
    app.state.project_repository = repository
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    client = TestClient(app)

    create = client.post(
        "/projects",
        json={"project_id": "api_project", "name": "API Project", "project_root": str(tmp_path / "projects" / "api_project"), "default_world_id": "mist_valley"},
    )
    assert create.status_code == 200
    assert client.get("/projects").json()["projects"][0]["project_id"] == "api_project"
    assert client.get("/projects/api_project/modes").status_code == 200
    assert client.post("/projects/api_project/validate").status_code == 200

    start = client.post("/projects/api_project/world/start", json={"world_id": "mist_valley"})
    assert start.status_code == 200
    payload = start.json()
    assert payload["visible_state"]["world_id"] == "mist_valley"
    assert "hidden_facts" not in json.dumps(payload).lower()
    state = client.get(f"/projects/api_project/world/state/{payload['session_id']}")
    assert state.status_code == 200

    legacy = client.post("/game/start", json={"world_id": "mist_valley"})
    assert legacy.status_code == 200


def test_v21_cli_tools(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path)
    project = repository.create_project(NarrativeProject(project_id="cli_project", name="CLI", project_root=str(tmp_path / "cli_project")))
    validate = subprocess.run(
        [sys.executable, "-m", "app.tools.validate_project", str(project.project_root), "--json"],
        cwd=Path("backend"),
        text=True,
        capture_output=True,
        check=False,
    )
    assert validate.returncode == 0, validate.stderr
    quality = subprocess.run(
        [sys.executable, "-m", "app.tools.project_quality_gate", str(project.project_root), "--json", "--skip-world-quality-gate"],
        cwd=Path("backend"),
        text=True,
        capture_output=True,
        check=False,
    )
    assert quality.returncode == 0, quality.stderr


def _tamper_checksum(archive_base64: str) -> str:
    raw = base64.b64decode(archive_base64)
    out = BytesIO()
    with ZipFile(BytesIO(raw)) as source, ZipFile(out, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "project_package_manifest.json":
                payload = json.loads(data.decode("utf-8"))
                first = payload["included_sections"][0]
                payload["checksums"][first] = "bad"
                data = json.dumps(payload).encode("utf-8")
            target.writestr(name, data)
    return base64.b64encode(out.getvalue()).decode("ascii")


def _zip_slip_archive() -> str:
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        archive.writestr("project_package_manifest.json", "{}")
        archive.writestr("../evil.txt", "evil")
    return base64.b64encode(out.getvalue()).decode("ascii")


def _executable_archive() -> str:
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        manifest = {
            "package_id": "bad",
            "project_id": "bad",
            "project_name": "Bad",
            "included_sections": ["run.exe"],
            "checksums": {"run.exe": "bad"},
        }
        archive.writestr("project_package_manifest.json", json.dumps(manifest))
        archive.writestr("run.exe", b"binary")
    return base64.b64encode(out.getvalue()).decode("ascii")
