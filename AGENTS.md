# Local LLM Interactive Novel World Engine

## 项目定位

这是一个本地自用的互动小说世界引擎。LLM 通过 API 提供，但世界状态、事件日志、存档、规则判定全部在本地执行。

## 核心架构原则

1. LLM 是叙事者，不是世界裁判。
2. 世界引擎是唯一事实源。
3. GameState 不能被 LLM 直接修改。
4. 所有状态变化必须通过 StateDelta。
5. 所有玩家行动必须生成 Event。
6. Event 必须能用于回放、调试、存档恢复。
7. 重要事实必须结构化保存，不能只存在自然语言文本中。
8. NPC 不能知道 npc_knowledge 以外的信息。
9. 玩家不能看到 player_visible_facts 以外的信息。
10. Prompt 不能代替代码规则。

## 开发规范

1. Python 代码必须使用类型标注。
2. 数据模型使用 Pydantic 或 SQLModel。
3. 每个核心模块必须有 pytest 测试。
4. 不允许硬编码 API key。
5. 不允许把 .env、数据库文件、日志文件提交到版本控制。
6. 不允许删除已有测试，除非明确说明原因并替换成更好的测试。
7. 修改前先阅读相关文档和现有代码。
8. 每次任务完成后，必须说明：
   - 修改了哪些文件
   - 增加了哪些功能
   - 如何运行测试
   - 还有哪些未完成事项

## 项目目录约定

- `backend/app/core`：世界状态、事件日志、StateDelta、游戏循环
- `backend/app/engine`：动作解析、规则系统、世界模拟
- `backend/app/llm`：LLM provider、意图解析、叙事渲染、记忆总结
- `backend/app/db`：数据库模型和会话
- `backend/tests`：后端测试
- `docs`：设计文档
- `worlds`：世界包内容

## 禁止事项

1. 不要让 LLM 输出直接写入 GameState。
2. 不要在业务代码中直接调用具体模型，必须经过 LLMProvider。
3. 不要在叙事文本中泄露隐藏事实。
4. 不要把游戏规则只写在 Prompt 中。
5. 不要把具体世界内容写死在引擎代码中。
6. 不要在没有测试的情况下修改 StateDelta、EventLog、GameState 核心逻辑。

## 完成标准

1. 代码能运行。
2. 测试能通过。
3. schema 校验明确。
4. 错误处理合理。
5. 文档与代码一致。
6. 变更范围尽量小，避免无关重构。
