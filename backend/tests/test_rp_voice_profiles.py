from pathlib import Path
from shutil import copytree

from app.core.world_state import GameState, NPCState, RPProfile, VoiceProfile, load_game_state_payload
from app.engine.content.validator import validate_world_pack
from app.engine.content.world_loader import WorldLoader
from app.llm.context_builder import build_npc_dialogue_profile_context
from app.session_store import build_visible_state


def _copy_worlds(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds"), worlds_root, dirs_exist_ok=True)
    return worlds_root


def test_npcs_yaml_rp_profile_loads(tmp_path: Path) -> None:
    worlds_root = _copy_worlds(tmp_path)
    npcs_path = worlds_root / "mist_valley" / "npcs.yaml"
    content = npcs_path.read_text(encoding="utf-8")
    content = content.replace(
        "    personality: Wary, practical, and slow to trust strangers.\n",
        """    personality: Wary, practical, and slow to trust strangers.
    rp_profile:
      public_persona: A guarded village blacksmith.
      private_self_summary: Secretly fears the bridge will collapse.
      attachment_style: slow trust
      trust_expression_style: practical help
      conflict_expression_style: clipped warnings
      intimacy_expression_style: quiet loyalty
      deception_style: avoids direct lies
      boundaries:
        - no needless violence
    voice_profile:
      tone: gravelly and careful
      sentence_length: short
      vocabulary_style: plain village craft terms
      catchphrases:
        - Measure twice.
      speech_habits:
        - pauses before naming danger
      silence_style: lets hammer taps fill gaps
      emotional_tells:
        - looks toward the bridge
    dialogue_style: terse but protective
    speech_habits:
      - answers with practical examples
    taboo_topics:
      - hidden_fact:mayor_hides_missing_tools
    emotional_mask: stoic
    example_dialogue_refs:
      - harlan_warning_example
""",
    )
    npcs_path.write_text(content, encoding="utf-8")

    pack = WorldLoader(worlds_root).load("mist_valley")
    npc = next(item for item in pack.npcs if item.id == "harlan")
    state = pack.to_game_state()

    assert npc.rp_profile.public_persona == "A guarded village blacksmith."
    assert state.npcs["harlan"].voice_profile.catchphrases == ["Measure twice."]


def test_missing_rp_profile_uses_safe_defaults() -> None:
    npc = NPCState(id="harlan", location_id="square")

    assert npc.rp_profile == RPProfile()
    assert npc.voice_profile == VoiceProfile()
    assert npc.taboo_topics == []


def test_voice_profile_safe_fields_enter_dialogue_context() -> None:
    state = GameState(
        world_id="test_world",
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                rp_profile=RPProfile(public_persona="Guarded blacksmith.", private_self_summary="Hidden grief."),
                voice_profile=VoiceProfile(
                    tone="low and rough",
                    sentence_length="short",
                    vocabulary_style="plain",
                    catchphrases=["Measure twice."],
                    speech_habits=["answers slowly"],
                    silence_style="long pauses",
                    emotional_tells=["rubs soot from his hands"],
                ),
                dialogue_style="terse",
                speech_habits=["uses forge metaphors"],
                taboo_topics=["hidden_fact:mayor_hides_missing_tools"],
                emotional_mask="stoic",
                example_dialogue_refs=["harlan_warning_example"],
            )
        }
    )

    context = build_npc_dialogue_profile_context(state, "harlan")

    assert context.public_persona == "Guarded blacksmith."
    assert context.tone == "low and rough"
    assert context.catchphrases == ["Measure twice."]
    assert "answers slowly" in context.speech_habits
    assert "uses forge metaphors" in context.speech_habits
    assert context.private_self_summary if hasattr(context, "private_self_summary") else None is None
    assert context.taboo_topic_count == 1
    assert "mayor_hides_missing_tools" not in context.model_dump_json()


def test_private_self_summary_not_in_player_visible_state() -> None:
    state = GameState(
        world_id="test_world",
        player={"location_id": "square"},
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                rp_profile=RPProfile(
                    public_persona="Helpful smith.",
                    private_self_summary="Hidden fear of the old bridge.",
                ),
                voice_profile=VoiceProfile(tone="warm"),
            )
        },
    )

    visible = build_visible_state(state)
    payload = visible.model_dump_json()

    assert "harlan" in payload
    assert "Hidden fear" not in payload
    assert "private_self_summary" not in payload
    assert "voice_profile" not in payload


def test_taboo_topic_does_not_expand_npc_knowledge() -> None:
    state = GameState(
        world_id="test_world",
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                knowledge=[],
                taboo_topics=["hidden_fact:mayor_hides_missing_tools"],
            )
        }
    )

    context = build_npc_dialogue_profile_context(state, "harlan")

    assert "mayor_hides_missing_tools" not in state.npcs["harlan"].knowledge
    assert "mayor_hides_missing_tools" not in context.model_dump_json()


def test_validate_world_catches_invalid_voice_profile(tmp_path: Path) -> None:
    worlds_root = _copy_worlds(tmp_path)
    npcs_path = worlds_root / "mist_valley" / "npcs.yaml"
    content = npcs_path.read_text(encoding="utf-8")
    content = content.replace(
        "    personality: Wary, practical, and slow to trust strangers.\n",
        """    personality: Wary, practical, and slow to trust strangers.
    voice_profile:
      sentence_length: enormous
""",
    )
    npcs_path.write_text(content, encoding="utf-8")

    report = validate_world_pack("mist_valley", worlds_root=worlds_root)

    assert not report.ok
    assert any("sentence_length" in issue.message for issue in report.errors)


def test_save_load_keeps_rp_and_voice_profiles() -> None:
    state = GameState(
        world_id="test_world",
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                rp_profile=RPProfile(public_persona="Steady smith."),
                voice_profile=VoiceProfile(tone="dry", sentence_length="medium"),
            )
        }
    )

    restored = load_game_state_payload(state.model_dump(mode="json"))

    assert restored.npcs["harlan"].rp_profile.public_persona == "Steady smith."
    assert restored.npcs["harlan"].voice_profile.tone == "dry"
