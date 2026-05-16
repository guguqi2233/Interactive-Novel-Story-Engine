import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  fetchGameState,
  GameInputResponse,
  startGame,
  submitPlayerInput,
  VisibleState
} from "./api";

type StoryEntry = {
  id: number;
  text: string;
};

export function App() {
  const [sessionId, setSessionId] = useState<string>("");
  const [visibleState, setVisibleState] = useState<VisibleState>({});
  const [turn, setTurn] = useState<number>(0);
  const [story, setStory] = useState<StoryEntry[]>([]);
  const [suggestedActions, setSuggestedActions] = useState<string[]>([]);
  const [input, setInput] = useState<string>("");
  const [debugOpen, setDebugOpen] = useState<boolean>(true);
  const [lastResponse, setLastResponse] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    void handleStart();
  }, []);

  const visibleFacts = useMemo(
    () => visibleState.visible_facts ?? [],
    [visibleState.visible_facts]
  );

  async function handleStart() {
    setIsLoading(true);
    setError("");
    try {
      const response = await startGame();
      setSessionId(response.session_id);
      setVisibleState(response.visible_state);
      setTurn(response.turn);
      setSuggestedActions(["观察四周", "去铁匠铺", "等待片刻"]);
      setStory([
        {
          id: Date.now(),
          text: "新的故事已经开始。"
        }
      ]);
      setLastResponse(response);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || !sessionId || isLoading) {
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await submitPlayerInput(sessionId, trimmedInput);
      applyGameInputResponse(response);
      setInput("");
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRefreshState() {
    if (!sessionId || isLoading) {
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await fetchGameState(sessionId);
      setVisibleState(response.visible_state);
      setTurn(response.turn);
      setLastResponse(response);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  function applyGameInputResponse(response: GameInputResponse) {
    setStory((entries) => [
      ...entries,
      {
        id: Date.now(),
        text: response.narrative_text
      }
    ]);
    setSuggestedActions(response.suggested_actions);
    setVisibleState(response.visible_state);
    setTurn(response.turn);
    setLastResponse(response);
  }

  return (
    <main className="app-shell">
      <aside className="side-panel">
        <div>
          <h1>雾谷</h1>
          <p className="muted">本地互动小说原型</p>
        </div>

        <section>
          <h2>当前地点</h2>
          <p>{visibleState.location_name ?? visibleState.location_id ?? "未开始"}</p>
        </section>

        <section>
          <h2>时间</h2>
          <p>Turn {turn}</p>
        </section>

        <section>
          <h2>背包</h2>
          <p className="muted">暂未接入</p>
        </section>

        <section>
          <h2>任务</h2>
          <p className="muted">暂未接入</p>
        </section>
      </aside>

      <section className="story-panel">
        <div className="story-scroll">
          {story.map((entry) => (
            <article className="story-entry" key={entry.id}>
              {entry.text}
            </article>
          ))}
          {story.length === 0 && <p className="muted">正在创建本地游戏会话...</p>}
        </div>

        {suggestedActions.length > 0 && (
          <div className="suggestions">
            {suggestedActions.map((action) => (
              <button type="button" key={action} onClick={() => setInput(action)}>
                {action}
              </button>
            ))}
          </div>
        )}

        <form className="input-row" onSubmit={handleSubmit}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="输入你的行动..."
            disabled={isLoading || !sessionId}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            发送
          </button>
        </form>

        {error && <p className="error">{error}</p>}
      </section>

      <aside className={`debug-panel ${debugOpen ? "open" : "closed"}`}>
        <button className="debug-toggle" type="button" onClick={() => setDebugOpen(!debugOpen)}>
          {debugOpen ? "收起 Debug" : "Debug"}
        </button>

        {debugOpen && (
          <div className="debug-content">
            <button type="button" onClick={handleRefreshState} disabled={!sessionId || isLoading}>
              刷新状态
            </button>
            <dl>
              <dt>Session</dt>
              <dd>{sessionId || "未创建"}</dd>
              <dt>可见事实</dt>
              <dd>{visibleFacts.length > 0 ? visibleFacts.join(", ") : "无"}</dd>
            </dl>
            <pre>{JSON.stringify({ visibleState, lastResponse }, null, 2)}</pre>
          </div>
        )}
      </aside>
    </main>
  );
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "请求失败。";
}
