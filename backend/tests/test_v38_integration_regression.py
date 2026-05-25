from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.provider_factory import create_llm_provider
from app.llm.provider_model_assignment import ProviderModelAssignmentRepository, validate_provider_model_assignments
from app.llm.provider_profiles import ModelProfile, ProviderProfileRepository, ProviderProfileV2
from app.llm.provider_router import ProviderRoutingConfig, ProviderRoutingRule
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


ROOT = Path(__file__).resolve().parents[2]
SECRET_LIKE_RE = re.compile(
    r"sk-(?!test-|fake-|redacted-)[A-Za-z0-9_-]{16,}|Authorization\s*:\s*Bearer\s+(?!\[redacted\])\S+",
    re.IGNORECASE,
)


def _frontend(path: str) -> str:
    return (ROOT / "frontend" / path).read_text(encoding="utf-8")


def _slice(source: str, start_token: str, end_token: str) -> str:
    start = source.find(start_token)
    assert start >= 0, f"Missing slice start: {start_token}"
    end = source.find(end_token, start + len(start_token))
    return source[start : end if end > start else start + 80_000]


def _project_repo(tmp_path: Path) -> ProjectRepository:
    root = tmp_path / "projects"
    project_root = root / "demo"
    repo = ProjectRepository(root)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    return repo


def _client(tmp_path: Path, *, debug_enabled: bool = False) -> tuple[TestClient, object, object]:
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = _project_repo(tmp_path)
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=debug_enabled, llm_provider="mock")
    return TestClient(app), previous_repo, previous_settings


def _restore(previous_repo: object, previous_settings: object) -> None:
    if previous_repo is None:
        if hasattr(app.state, "project_repository"):
            delattr(app.state, "project_repository")
    else:
        app.state.project_repository = previous_repo
    app.state.settings = previous_settings or Settings(llm_provider="mock")


def test_v38_frontend_routes_and_product_surfaces_remain_integrated() -> None:
    app_source = _frontend("src/App.tsx")
    api_source = _frontend("src/api.ts")
    provider_source = _frontend("src/providerUi.tsx")
    package_json = json.loads(_frontend("package.json"))

    home = _slice(app_source, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel")
    navigation = _slice(app_source, "function UnifiedNavigation", "function LocalStatusBar")
    provider_wizard = _slice(provider_source, "function ProviderSetupWizard", "function ProviderConnectivityDashboard")
    safe_surface = "\n".join([home, navigation, provider_wizard])

    for token in (
        'data-testid="v37-cn-playable-home"',
        "写小说",
        "角色 RP",
        "大世界游玩",
        "data-testid=\"v37-advanced-tools-nav\"",
        "data-default-collapsed=\"true\"",
        "调试 / 回放",
        "data-testid=\"v38-backend-unavailable-state\"",
        "本地后端未连接",
        "data-testid=\"v38-provider-missing-cta\"",
        "配置模型服务",
    ):
        assert token in app_source + provider_source

    for token in (
        'lazyNamed(() => import("./providerUi")',
        'lazyNamed(() => import("./novelUi")',
        'lazyNamed(() => import("./tavernUi")',
        'lazyNamed(() => import("./worldUi")',
        "<Suspense",
        "<AppErrorBoundary",
    ):
        assert token in app_source

    for token in ("fetchProjectProviderModels", "syncProjectProviderModels", "saveProjectProviderModelAssignments"):
        assert token in api_source
    assert "check:v38-integration-regression" in package_json["scripts"]

    assert "TimelineReplayPanel" not in home
    assert "StateDeltaViewerPanel" not in home
    assert "EventLogViewerPanel" not in home
    assert "Product Readiness Dashboard" not in home
    assert "raw_state_deltas" not in home
    assert "state_deltas.map" not in home
    assert not SECRET_LIKE_RE.search(safe_surface)
    assert "hidden_fact_text" not in safe_surface
    assert "npc_secret" not in safe_surface
    assert not re.search(r"create(Account|CloudSync|OnlineMarketplace|RemoteDownload)", app_source + provider_source)


def test_v38_fake_provider_and_model_assignment_still_work_without_network(tmp_path: Path) -> None:
    provider = create_llm_provider(Settings(llm_provider="local_stub"))
    assert provider.generate_text([{"role": "user", "content": "hello"}]) == "local stub text"

    profile = ProviderProfileV2(
        provider_profile_id="local_stub",
        display_name="Local Stub",
        provider_type="local_stub",
        requires_api_key=False,
        model_profiles=[ModelProfile(model_id="json-pro", supports_json=True, supports_text=True)],
    )
    ProviderProfileRepository(tmp_path).save_provider_profile(profile)
    saved = ProviderModelAssignmentRepository(tmp_path).save(
        ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case="world_intent_parse",
                    primary_provider_id="local_stub",
                    primary_model_id="json-pro",
                    require_json_support=True,
                    require_local_only=True,
                ),
                ProviderRoutingRule(
                    use_case="novel_draft",
                    primary_provider_id="local_stub",
                    primary_model_id="json-pro",
                    require_local_only=True,
                ),
                ProviderRoutingRule(
                    use_case="tavern_reply",
                    primary_provider_id="local_stub",
                    primary_model_id="json-pro",
                    require_local_only=True,
                ),
            ]
        )
    )
    validation = validate_provider_model_assignments(saved, [profile])
    rendered = json.dumps(
        {
            "profile": profile.safe_summary(),
            "assignment": saved.model_dump(mode="json"),
            "validation": validation.model_dump(mode="json"),
        },
        ensure_ascii=False,
    )

    assert not validation.warnings
    assert "world_intent_parse" in {str(rule.use_case) for rule in validation.rules}
    assert not SECRET_LIKE_RE.search(rendered)
    assert "api_key':" not in rendered.lower()
    assert '"api_key":' not in rendered.lower()
    assert "sk-" not in rendered


def test_v38_world_action_uses_backend_api_and_debug_route_remains_gated(tmp_path: Path) -> None:
    client, previous_repo, previous_settings = _client(tmp_path, debug_enabled=False)
    try:
        start = client.post("/game/start", json={"world_id": "mist_valley"})
        assert start.status_code == 200
        session_id = start.json()["session_id"]

        action = client.post("/game/input", json={"session_id": session_id, "player_input": "look around"})
        state = client.get(f"/game/state/{session_id}")
        debug_events = client.get(f"/debug/sessions/{session_id}/events")
    finally:
        _restore(previous_repo, previous_settings)

    assert action.status_code == 200
    assert state.status_code == 200
    assert "visible_state" in state.text
    assert "state_deltas" not in state.text
    assert "npc_knowledge" not in state.text
    assert debug_events.status_code == 403
