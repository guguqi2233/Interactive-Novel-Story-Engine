import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, NPCState
from app.llm.context_inspector import ContextInspectRequest, ContextInspectType, inspect_context
from app.llm.memory_store import MemoryRecord, MemoryVisibility
from app.main import app


SECRET_TEXT = "the mayor forged the charter"


def _state() -> GameState:
    return GameState(
        world_id="inspect_world",
        locations={"square": LocationState(id="square", name="Square")},
        npcs={"mira": NPCState(id="mira", location_id="square", knowledge=["public_fact"])},
        facts={
            "public_fact": FactState(id="public_fact", text="A public bell rings.", visibility=FactVisibility.PUBLIC, public=True),
            "hidden_fact": FactState(id="hidden_fact", text=SECRET_TEXT, visibility=FactVisibility.HIDDEN),
        },
        player_visible_facts={"public_fact"},
    )


def test_narrator_context_snapshot_can_be_generated() -> None:
    snapshot = inspect_context(
        ContextInspectRequest(
            context_type=ContextInspectType.NARRATOR,
            state=_state(),
            location_id="square",
            npc_id="mira",
            memories=[MemoryRecord(id="m1", content="A safe visible memory.", visibility=MemoryVisibility.NARRATOR_SAFE)],
        )
    )

    assert snapshot.context_type == ContextInspectType.NARRATOR
    assert snapshot.total_token_estimate > 0
    assert any(section.section_type == "visible_facts" for section in snapshot.sections)


def test_hidden_fact_is_redacted() -> None:
    snapshot = inspect_context(ContextInspectRequest(context_type=ContextInspectType.NARRATOR, state=_state(), location_id="square", npc_id="mira"))
    payload = json.dumps(snapshot.model_dump_safe(), ensure_ascii=False)

    assert SECRET_TEXT not in payload
    assert any("hidden_fact" in section.safe_summary for section in snapshot.sections)
    assert any(section.content_redacted == "[redacted:hidden]" for section in snapshot.sections)


def test_npc_unknown_fact_is_excluded() -> None:
    snapshot = inspect_context(ContextInspectRequest(context_type=ContextInspectType.DIALOGUE, state=_state(), location_id="square", npc_id="mira"))

    reasons = [reason for section in snapshot.sections for reason in section.excluded_reasons]
    assert "npc_unknown_fact:hidden_fact" in reasons
    assert not any(SECRET_TEXT in section.content_redacted for section in snapshot.sections)


def test_token_estimate_exists() -> None:
    snapshot = inspect_context(ContextInspectRequest(context_type=ContextInspectType.INTENT_PARSER, state=_state(), location_id="square", player_input="look"))

    assert snapshot.total_token_estimate > 0
    assert all(section.token_estimate >= 0 for section in snapshot.sections)


def test_raw_prompt_default_not_returned_and_debug_is_redacted() -> None:
    default_snapshot = inspect_context(ContextInspectRequest(context_type=ContextInspectType.NARRATOR, state=_state(), location_id="square"))
    debug_snapshot = inspect_context(
        ContextInspectRequest(
            context_type=ContextInspectType.NARRATOR,
            state=_state(),
            location_id="square",
            include_debug_raw=True,
        )
    )

    assert default_snapshot.raw_prompt_redacted is None
    assert debug_snapshot.raw_prompt_redacted is not None
    assert SECRET_TEXT not in debug_snapshot.raw_prompt_redacted


def test_context_inspector_api_respects_gate() -> None:
    previous_settings = getattr(app.state, "settings", None)
    client = TestClient(app)
    try:
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post("/prompt-lab/context/inspect", json={"context_type": "narrator"})
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        enabled = client.post(
            "/prompt-lab/context/inspect",
            json={"context_type": "narrator", "state": _state().model_dump(mode="json"), "location_id": "square"},
        )
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")

    assert disabled.status_code == 403
    assert enabled.status_code == 200
    assert SECRET_TEXT not in enabled.text
    assert enabled.json()["total_token_estimate"] > 0
