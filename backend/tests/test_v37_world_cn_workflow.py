from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
FRONTEND = REPO_ROOT / "frontend"


def _client(tmp_path: Path) -> TestClient:
    database_path = tmp_path / "v37_world_cn.sqlite"
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(database_path)
    app.state.settings = Settings(
        database_url=f"sqlite:///{database_path}",
        llm_provider="mock",
        enable_debug_api=False,
        enable_authoring_api=True,
        enable_module_api=True,
        enable_eval_api=True,
        enable_playtest_api=True,
    )
    return TestClient(app)


def test_v37_world_cn_game_input_uses_player_api_and_visible_state_only(tmp_path: Path) -> None:
    client = _client(tmp_path)

    start = client.post("/game/start", json={"world_id": "mist_valley"})
    assert start.status_code == 200, start.text
    session_id = start.json()["session_id"]
    assert "visible_state" in start.json()

    action = client.post("/game/input", json={"session_id": session_id, "player_input": "search"})
    assert action.status_code == 200, action.text
    payload = action.json()

    assert "visible_state" in payload
    assert "suggested_actions" in payload
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert "state_deltas" not in serialized
    assert "npc secret" not in serialized
    assert "debug memory" not in serialized
    assert "authorization" not in serialized
    assert "api_key" not in serialized

    game_loop = app.state.session_store.get_session(session_id)
    assert game_loop is not None
    assert game_loop.event_log.list_events()
    assert any(event.state_deltas for event in game_loop.event_log.list_events())


def test_v37_world_cn_frontend_workflow_copy_and_boundaries() -> None:
    app_source = (FRONTEND / "src" / "App.tsx").read_text(encoding="utf-8")
    world_source = (FRONTEND / "src" / "worldUi.tsx").read_text(encoding="utf-8")
    package_source = (FRONTEND / "package.json").read_text(encoding="utf-8")
    combined = f"{app_source}\n{world_source}"

    for token in [
        "本地大世界入口",
        "继续大世界",
        "开始大世界",
        "配置模型服务",
        "行动输入 / 建议行动",
        "玩家输入通过 /game/input 提交",
        "LLM 只做意图解析与叙事渲染",
        "世界输入解析模型",
        "世界叙事渲染模型",
        "普通视图只使用 visible_state",
        'data-testid="v37-world-cn-home"',
        'data-testid="v37-world-cn-start-continue"',
        'data-testid="v37-world-cn-provider-warning"',
        '"check:v37-world-cn-workflow"',
    ]:
        assert token in combined or token in package_source

    assert "submitPlayerInput(sessionId" in app_source
    assert "requestJson<GameInputResponse>(\"/game/input\"" in (FRONTEND / "src" / "api.ts").read_text(encoding="utf-8")
    assert not re.search(r"<input[^>]+(?:name|id)=['\"]api[_-]?key['\"]", combined, flags=re.IGNORECASE)
    normal_world_source = world_source.split("export function DebugGate", maxsplit=1)[0]
    assert "JSON.stringify(event.state_deltas" not in normal_world_source
    assert "setGameState(" not in normal_world_source
    assert "applyStateDelta" not in normal_world_source
