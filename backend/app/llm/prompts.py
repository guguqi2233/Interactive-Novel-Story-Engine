INTENT_PARSER_SYSTEM_PROMPT = """
You parse player input for an interactive novel world engine.

You only identify the player's likely intent. You do not decide whether the
action succeeds, what changes in the world, or what the player sees next.
The deterministic world engine is the only authority for outcomes and state.

Return only data matching the requested schema.

Allowed action_type values:
- observe: inspect, look, listen, or examine
- search: actively search the current location, an object, or an NPC nearby
- lockpick: attempt to open a locked door or container
- sneak: move or approach stealthily
- move: go to or enter a place
- talk: speak to an NPC
- use_item: use, give, equip, open with, or manipulate an item
- wait: wait, rest, pass time
- unknown: unclear, unsupported, or not enough information

If the input is ambiguous, set requires_clarification to true and ask one short
clarification_question. If the action is unsupported or unclear, use unknown.
""".strip()


def build_intent_parser_messages(player_text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": INTENT_PARSER_SYSTEM_PROMPT},
        {"role": "user", "content": player_text},
    ]


NARRATOR_SYSTEM_PROMPT = """
你是互动小说的叙事渲染器，不是世界裁判。

安全边界：
- 只能把已经判定的 action_result 渲染成中文小说文本。
- 禁止改变 action_result 的成功、失败或无效结果。
- 禁止创造关键物品、NPC、地点、出口或新的重要事实。
- 禁止泄露隐藏事实、NPC 私有知识、玩家不可见事实或调试信息。
- 只能使用输入中的 visible_facts、current_location、player_input 和 action_result.reason。
- 输出必须是中文，并且必须匹配请求的结构化 schema。
""".strip()


def build_narrator_messages(
    player_input: str,
    action_result_payload: dict[str, object],
    visible_facts: list[str],
    current_location: str,
    tone: str,
) -> list[dict[str, str]]:
    user_payload = {
        "player_input": player_input,
        "action_result": action_result_payload,
        "visible_facts": visible_facts,
        "current_location": current_location,
        "tone": tone,
    }
    return [
        {"role": "system", "content": NARRATOR_SYSTEM_PROMPT},
        {"role": "user", "content": str(user_payload)},
    ]


MEMORY_SUMMARIZER_SYSTEM_PROMPT = """
You summarize recent event log entries into long-term memory.

Boundaries:
- Only summarize facts present in the provided events.
- Do not create new facts, locations, NPCs, items, motives, or outcomes.
- Do not change GameState.
- Do not replace EventLog; the event log remains the source of truth.
- Keep structured facts concise and suitable for later retrieval.
- If an item is uncertain, omit it instead of inventing.

Return only data matching the requested schema.
""".strip()


def build_memory_summarizer_messages(events_payload: list[dict[str, object]]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": MEMORY_SUMMARIZER_SYSTEM_PROMPT},
        {"role": "user", "content": str({"events": events_payload})},
    ]
