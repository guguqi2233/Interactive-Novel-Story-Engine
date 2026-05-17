from pathlib import Path

from fastapi.testclient import TestClient

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    CrimeState,
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    RumorState,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.content.side_quest_generator import (
    QuestDraft,
    QuestDraftStage,
    validate_quest_draft,
)
from app.engine.content.world_loader import WorldLoader
from app.llm.context_builder import MemoryContextBuilder
from app.llm.fake_provider import FakeLLMProvider
from app.llm.memory_store import InMemoryMemoryStore, MemoryRecord, MemoryVisibility
from app.llm.narrator import Narrator
from app.llm.schemas import NarrativeResult
from app.main import app
from app.session_store import InMemorySessionStore, build_visible_state


SECRET_FACT_ID = "sealed_letter_under_stone"
SECRET_FACT_TEXT = "A sealed letter is hidden beneath a loose paving stone."
NPC_SECRET = "harlan_knows_the_smugglers_route"
HIDDEN_WITNESS_ID = "hidden_watcher"
DEBUG_MEMORY_TEXT = "debug-only raw witness trace"
HIDDEN_MEMORY_TEXT = "hidden memory about the sealed letter"
RAW_DELTA_PATH = "npcs.hidden_watcher.secrets"


class RecordingNarratorProvider(FakeLLMProvider):
    def __init__(self) -> None:
        super().__init__(
            json_responses=[
                {
                    "text": "You notice only what is in front of you.",
                    "suggested_actions": ["observe"],
                    "short_summary": "The visible scene was described.",
                }
            ]
        )
        self.messages: list[dict[str, str]] = []

    def generate_json(
        self,
        messages: list[dict[str, str]],
        schema: type[NarrativeResult],
        temperature: float = 0.2,
    ) -> NarrativeResult:
        self.messages = messages
        return super().generate_json(messages, schema, temperature)


def make_boundary_state() -> GameState:
    return GameState(
        world_id="boundary-eval",
        locations={"square": LocationState(id="square", name="Square")},
        player_visible_facts={"public_square"},
        facts={
            "public_square": FactState(
                id="public_square",
                text="The square is open and quiet.",
                visibility=FactVisibility.PUBLIC,
                public=True,
            ),
            SECRET_FACT_ID: FactState(
                id=SECRET_FACT_ID,
                text=SECRET_FACT_TEXT,
                visibility=FactVisibility.HIDDEN,
                secret=True,
                known_by={"harlan"},
            ),
        },
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                knowledge=[SECRET_FACT_ID],
                secrets=[NPC_SECRET],
            ),
            HIDDEN_WITNESS_ID: NPCState(
                id=HIDDEN_WITNESS_ID,
                location_id="square",
                hidden=True,
                visible=True,
                secrets=["saw_the_player"],
            ),
        },
        crimes={
            "crime-1": CrimeState(
                id="crime-1",
                crime_type="theft",
                actor_id="player",
                location_id="square",
                witnessed_by=[HIDDEN_WITNESS_ID],
            )
        },
    )


def test_hidden_fact_does_not_enter_narrator_prompt() -> None:
    provider = RecordingNarratorProvider()
    narrator = Narrator(provider)

    narrator.render(
        player_input="look around",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Observed current location.",
            visible_facts=["public_square"],
            hidden_facts=[SECRET_FACT_ID, SECRET_FACT_TEXT],
        ),
        visible_facts=["public_square"],
        current_location="square",
        tone="plain",
    )

    prompt_snapshot = str(provider.messages)
    assert "public_square" in prompt_snapshot
    assert SECRET_FACT_ID not in prompt_snapshot
    assert SECRET_FACT_TEXT not in prompt_snapshot
    assert "hidden_facts" not in prompt_snapshot


def test_npc_secret_does_not_enter_narrator_prompt() -> None:
    provider = RecordingNarratorProvider()
    narrator = Narrator(provider)

    narrator.render(
        player_input="talk to Harlan",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Conversation can begin.",
            visible_facts=["harlan", "mood:neutral"],
            hidden_facts=[NPC_SECRET],
        ),
        visible_facts=["harlan", "mood:neutral"],
        current_location="square",
        tone="plain",
    )

    prompt_snapshot = str(provider.messages)
    assert "harlan" in prompt_snapshot
    assert NPC_SECRET not in prompt_snapshot


def test_hidden_witness_does_not_enter_player_narrative_prompt() -> None:
    provider = RecordingNarratorProvider()
    narrator = Narrator(provider)

    narrator.render(
        player_input="take the ring",
        action_result=ActionResult(
            success_level=SuccessLevel.PARTIAL_SUCCESS,
            reason="The action has consequences.",
            visible_facts=["crime:public_noise"],
            hidden_facts=[HIDDEN_WITNESS_ID],
        ),
        visible_facts=["crime:public_noise"],
        current_location="square",
        tone="plain",
    )

    assert HIDDEN_WITNESS_ID not in str(provider.messages)


def test_debug_state_deltas_do_not_enter_player_api(tmp_path: Path) -> None:
    del tmp_path
    app.state.session_store = InMemorySessionStore()
    client = TestClient(app)
    session_id = client.post("/game/start").json()["session_id"]

    payload = client.post(
        "/game/input",
        json={"session_id": session_id, "player_input": "observe"},
    ).json()

    assert "state_deltas" not in str(payload)
    assert RAW_DELTA_PATH not in str(payload)


def test_hidden_and_debug_memory_do_not_enter_narrator_context() -> None:
    state = make_boundary_state()
    store = InMemoryMemoryStore(
        [
            MemoryRecord(
                id="safe",
                content="The square looked quiet.",
                visibility=MemoryVisibility.NARRATOR_SAFE,
                entity_ids=["location:square"],
                fact_ids=["public_square"],
            ),
            MemoryRecord(
                id="hidden",
                content=HIDDEN_MEMORY_TEXT,
                visibility=MemoryVisibility.HIDDEN,
                fact_ids=[SECRET_FACT_ID],
            ),
            MemoryRecord(
                id="debug",
                content=DEBUG_MEMORY_TEXT,
                visibility=MemoryVisibility.DEBUG_ONLY,
            ),
        ]
    )

    context = MemoryContextBuilder(store).build(
        state=state,
        actor_id="player",
        current_location="square",
        action_result=ActionResult(success_level=SuccessLevel.SUCCESS, reason="Observed."),
        visible_facts=["public_square"],
    )

    snapshot = str([memory.content for memory in context.narrator_safe_memories])
    assert "The square looked quiet." in snapshot
    assert HIDDEN_MEMORY_TEXT not in snapshot
    assert DEBUG_MEMORY_TEXT not in snapshot


def test_rumor_does_not_leak_hidden_fact_text_to_visible_state() -> None:
    state = make_boundary_state()
    state.rumors["rumor-1"] = RumorState(
        id="rumor-1",
        fact_id=SECRET_FACT_ID,
        known_by_player=True,
    )

    payload = build_visible_state(state).model_dump(mode="json")

    assert SECRET_FACT_TEXT not in str(payload)
    assert payload["known_rumors"][0]["text_for_player"] == (
        "You have heard a vague rumor, but not enough to confirm the details."
    )


def test_rumor_with_player_text_does_not_leak_hidden_fact_text_to_visible_state() -> None:
    state = make_boundary_state()
    state.rumors["rumor-1"] = RumorState(
        id="rumor-1",
        fact_id=SECRET_FACT_ID,
        text_for_player=f"People whisper that {SECRET_FACT_TEXT}",
        known_by_player=True,
    )

    payload = build_visible_state(state).model_dump(mode="json")

    assert SECRET_FACT_TEXT not in str(payload)
    assert payload["known_rumors"][0]["text_for_player"] == (
        "You have heard a vague rumor, but not enough to confirm the details."
    )


def test_procedural_quest_draft_does_not_leak_hidden_fact_text() -> None:
    pack = WorldLoader("worlds").load("mist_valley")
    draft = QuestDraft(
        title="Leaky Letter Draft",
        premise=SECRET_FACT_TEXT,
        required_facts=[SECRET_FACT_ID],
        stages=[QuestDraftStage(id="start", title="Start")],
    )

    report = validate_quest_draft(draft, pack)

    assert not report.ok
    assert any(issue.code == "hidden_fact_text_leak" for issue in report.errors)


def test_raw_state_delta_not_sent_to_narrator_prompt() -> None:
    provider = RecordingNarratorProvider()
    narrator = Narrator(provider)

    narrator.render(
        player_input="wait",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Time passes.",
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=RAW_DELTA_PATH,
                    value=["secret"],
                    reason="Debug hidden state change.",
                )
            ],
            visible_facts=["time:30"],
        ),
        visible_facts=["time:30"],
        current_location="square",
        tone="plain",
    )

    prompt_snapshot = str(provider.messages)
    assert "time:30" in prompt_snapshot
    assert RAW_DELTA_PATH not in prompt_snapshot
    assert "state_deltas" not in prompt_snapshot
