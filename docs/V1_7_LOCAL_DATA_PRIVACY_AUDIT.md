# v1.7 Local Data / Privacy Audit

## Verdict

v1.7 当前本地数据与隐私边界整体通过专项审查，未发现会阻塞 v1.7 acceptance 的高风险泄露路径。

本审查重点覆盖 Desktop Studio Boundary、启动脚本、前端配置、Local Config Manager、Workspace / Recent Projects、Health Check、Crash Report、desktop policy、backup/export policy 约束和相关测试。结论仅针对当前代码实现和本地文档，不代表未来完整安装器或云同步能力。

## Verification Date

2026-05-20

## Reviewed Areas

- `docs/DESKTOP_STUDIO_BOUNDARY.md`
- `docs/DESKTOP_PACKAGING.md`
- `backend/app/desktop/studio_policy.py`
- `backend/app/desktop/local_config.py`
- `backend/app/desktop/workspaces.py`
- `backend/app/desktop/health.py`
- `backend/app/desktop/crash_reports.py`
- `backend/app/desktop/startup_diagnostics.py`
- `scripts/start_local_studio.ps1`
- `scripts/start_local_studio.sh`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- v1.7 desktop/privacy-related tests

## 已通过项目

1. API key 不进入前端。
   前端 API 配置仅使用 `VITE_API_BASE_URL`；desktop policy 明确只允许该类安全前端配置，并拒绝 `VITE_*` 中出现 key/secret/token 类字段。

2. API key 不进入 logs。
   启动脚本不打印 key；desktop log redaction 策略会脱敏 `sk-...`、API key assignment、Authorization header 等敏感模式。日志默认位于本地 `logs/`。

3. API key 不进入 crash reports。
   `CrashReportService` 只保存 `safe_message`、`stack_redacted`、`context_safe_summary`，并过滤 API key、raw env、raw prompt、hidden fact text、password 等字段。

4. API key 不进入 backup bundle。
   `DesktopStudioPolicy.validate_backup_bundle` 拒绝 `.env`、数据库、日志、缓存、绝对路径、路径穿越和含 secret-like 内容的文件预览。

5. API key 不进入 world export。
   v1.7 desktop policy 对 export bundle 使用同类 secret/path 检查；既有 content/package safe export 边界也要求不导出 API key。

6. `.env` 不会被备份/导出。
   `.env`、`.env.local`、`.env.production` 被 policy 明确拒绝，`.gitignore` 和 packaging 文档也要求排除。

7. raw env 不进入 config summary。
   `LocalConfigSummary` 返回 provider type、model id、feature toggles、database configured yes/no 和 redacted paths，不返回 raw environment。

8. raw prompt 不进入 crash reports。
   crash report redaction 覆盖 `raw_prompt`、`prompt=`、hidden fact text 等模式。当前桌面层没有把 prompt 全文作为 normal report 暴露。

9. hidden facts 不进入 normal desktop reports。
   health/config/workspace/update/crash 等 v1.7 desktop summary 均使用 safe summary / redacted 字段，不读取或返回 world hidden fact 全文。

10. logs 默认本地保存。
    启动脚本写入本地 `logs/`，文档明确不上传日志；未发现日志上传路径。

11. crash reports 默认本地保存，不上传。
    crash report service 是本地存储/读取模型，未发现网络上传或外部发送逻辑。

12. health check 不返回 secrets。
    `DesktopHealthCheckReport` 使用 safe config summary，并将 provider issue 字段归一为安全摘要，避免暴露 key 值或 raw env。

13. project/recent paths 已 redacted。
    `ProjectWorkspace` 和 `RecentProjectEntry` 使用 `path_redacted`，普通前端不接收完整敏感路径。

14. frontend 不保存 secrets。
    当前前端未发现 `localStorage`、`sessionStorage`、cookie 存储 API key 或 raw env 的路径。

15. desktop scripts 不硬编码 secrets。
    启动脚本只包含安全提示和变量名，不包含真实 key；脚本不会把 `LLM_API_KEY` 注入前端环境。

16. backup/restore 覆盖保护已有边界。
    当前策略和文档要求 restore dry-run、checksum、冲突检测和显式确认；workspace template 创建也拒绝覆盖已有非空目录。

## 可能泄露路径

1. `/studio/config/issues` 可能返回配置字段名。
   `LocalConfigManager.check_provider_config` 的 issue 可能包含 `LLM_API_KEY` 这类字段名。它不是 secret value，也不泄露 key，但若按最严格隐私口径，可以把普通 UI 中的字段名统一显示为 `provider_config`。

2. safe export 对 hidden story text 的防护依赖调用方。
   Desktop policy 能拒绝 `.env`、API key、数据库、日志、缓存和 secret-like 内容，但无法独立理解任意世界包里的 hidden fact 语义。world export 必须继续走既有 safe export profile / validation / hidden redaction 流程。

3. `LOCAL_LLM_BASE_URL` 不应包含 credential。
   启动脚本会把 local provider base URL 传给后端进程。当前不会传给前端，但如果用户把 token 放进 URL，本地进程命令行或诊断摘要仍可能扩大暴露面。

4. Log Viewer / Backup Restore 的完整运行时能力仍需最终验收确认。
   当前已有 policy、文档和部分服务级防护；若后续补全完整 API/CLI，需要确保所有入口复用同一 redaction 和 bundle validation。

## 高风险泄露

未发现。

没有发现 API key 被写入前端、日志、crash report、backup bundle、world export 的直接路径；也未发现 crash report 或日志上传网络的逻辑。

## 中风险泄露

1. world export / backup 中 hidden fact 语义级脱敏需要由业务导出流程保证。
   Desktop policy 不是 world content semantic redactor。若某个导出路径绕过既有 safe export profile，可能把 hidden authoring text 当作普通内容打包。

2. 未来完整 Backup / Restore API 若未复用 policy，可能引入覆盖或泄露风险。
   当前文档与 policy 要求明确，但实现扩展时必须保持 dry-run、checksum、冲突检测、显式确认和 secret exclusion。

## 小问题

1. config issue 字段名可以进一步抽象。
   对普通 UI 来说，`LLM_API_KEY` 这类字段名可改为 `provider_config`，减少对具体 secret env name 的展示。

2. 建议把 log/crash/backup/export redaction 统一成共享 helper。
   当前多个模块都有 redaction 逻辑，长期维护时容易出现规则漂移。

3. 建议明确禁止 credential-in-URL。
   文档可补充：`LOCAL_LLM_BASE_URL` 不应包含 token、用户名密码或其他 credential。

4. 建议在最终冻结前扫描构建产物。
   尤其是 `frontend/dist`、desktop build outputs、backup artifacts 和 release artifacts，确认没有 `.env`、API key、raw env、raw prompt。

## 修复建议

1. 将 `/studio/config/issues` 的普通前端显示字段统一归一为安全标签，例如 `provider_config`。
2. 确保 One-click World Export 必须调用 safe export profile，并默认 `redact_hidden_text=true`。
3. Backup / Restore、World Export、Crash Report、Log Viewer 继续复用同一 secret/hidden redaction 策略。
4. 在 v1.7 freeze 前运行一次 artifact 扫描：`.env`、`sk-...`、database、logs、cache、frontend/dist、desktop build outputs。
5. 在文档中补充：本地 URL 配置不应嵌入 credential。

## 是否阻塞 v1.7

不阻塞 v1.7。

当前未发现高风险泄露。中风险项主要是后续完整 backup/export runtime 必须继续复用 safe profile、validation gate 和 redaction policy，属于验收关注点，不是当前 release blocker。
