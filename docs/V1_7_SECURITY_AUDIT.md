# v1.7 Security / Desktop Packaging Audit

## Verdict

v1.7 当前 security / desktop packaging 边界整体通过专项审查，未发现阻塞 v1.7 release 的高风险问题。

本审查覆盖 git 跟踪状态、`.gitignore`、启动脚本、前端配置、safe config summary、backup/export policy、crash report、health check、workspace selector、desktop packaging 文档和测试中的真实 API 调用风险。

## Verification Date

2026-05-20

## Evidence Reviewed

- `.gitignore`
- `git ls-files`
- `scripts/start_local_studio.ps1`
- `scripts/start_local_studio.sh`
- `frontend/src/api.ts`
- `backend/app/desktop/studio_policy.py`
- `backend/app/desktop/local_config.py`
- `backend/app/desktop/workspaces.py`
- `backend/app/desktop/health.py`
- `backend/app/desktop/crash_reports.py`
- `backend/app/desktop/startup_diagnostics.py`
- `docs/DESKTOP_PACKAGING.md`
- `docs/DESKTOP_STUDIO_BOUNDARY.md`
- v1.7 desktop/security tests

## 已通过项目

1. `.env` 未被 git 跟踪。
   `git ls-files` 未显示 `.env` 或 `frontend/.env`，`.gitignore` 明确排除 `.env` 与 `frontend/.env`。

2. 数据库、日志、缓存、`frontend/dist`、desktop build outputs 未被 git 跟踪。
   `git ls-files` 未显示 `.db`、`.sqlite`、`.log`、`logs/`、`cache/`、`frontend/dist/`、`desktop-dist/`、`desktop_build/` 等产物。

3. `backups/`、`crash-reports/`、`logs/` 已被 `.gitignore` 排除。
   `.gitignore` 包含 `logs/`、`crash-reports/`、`backups/`、`frontend/dist/`、`desktop-dist/`、`desktop_build/`、`release/`、数据库和缓存模式。

4. 启动脚本不硬编码 API key。
   Windows / shell 启动脚本只包含 `LLM_API_KEY` 的安全提示和缺失检查，不包含真实 key；脚本说明其不会读取、打印或注入 `LLM_API_KEY` 到前端。

5. 前端 build 不应包含 API key。
   前端 API 层只读取 `VITE_API_BASE_URL`；desktop policy 会拒绝 `VITE_LLM_API_KEY`、`VITE_OPENAI_API_KEY` 或其他 key/secret/token 类前端变量。

6. config summary 不返回 raw env。
   `LocalConfigManager.get_safe_summary` 返回 provider type、model id、feature toggles、database configured yes/no 和 redacted local paths，不返回 raw environment 或 secret value。

7. backup/export policy 排除 `.env`、API key、logs、cache、database。
   `DesktopStudioPolicy` 拒绝 `.env`、`.log`、`.db`、`.sqlite`、`.cache`、`logs/`、`.cache/`、`node_modules/`、`frontend/dist/`、desktop build dirs、绝对路径、路径穿越和 secret-like content preview。

8. restore / import 防 zip slip 的既有包系统已覆盖。
   v1.6 gameplay module package import 和 v1.4 package import 逻辑已有 zip slip/path traversal 检查；v1.7 Backup / Restore 文档要求 restore dry-run、checksum、冲突检测和显式确认。

9. restore / import 拒绝可执行文件的既有包系统已覆盖。
   gameplay module package、script package、import profile 等既有路径拒绝 executable files；v1.7 backup/restore 文档也要求默认拒绝可执行文件。

10. crash report viewer 会 redact secrets。
    `CrashReportService` redacts `sk-...`、Authorization bearer、API key assignment、password、raw env、raw prompt、hidden fact text，并过滤 context key 中的 api/key/secret/password/env/prompt/hidden。

11. health check 不泄露 secrets。
    `DesktopHealthCheckService` 使用 safe config summary、redacted workspace path 和 generic provider issue field，不返回 API key、raw env、hidden facts 或完整敏感路径。

12. workspace selector 防路径穿越。
    `WorkspaceService` 对 workspace add/create 拒绝 `..`、`.env`、`node_modules`、`logs`、`cache`、`dist` 等路径，并只向前端返回 `path_redacted`。

13. 未发现真实 `sk-...` key。
    扫描到的 `sk-...` 均出现在测试或文档中，格式为 `sk-test-*`、`sk-real-looking-*` 等假 key，用于 redaction 测试。

14. 测试假 key 不应被误判为真实泄露。
    测试中明确断言 fake key 不出现在 report、summary、package、usage、crash 输出中；这些值属于安全回归 fixture。

15. tests 默认不调用真实 API。
    v1.5/v1.6/v1.7 测试路径使用 mock/local_stub/fake provider；真实 provider benchmark 需要显式开启。

16. desktop packaging docs 明确本地原型边界。
    `docs/DESKTOP_PACKAGING.md` 明确这是 local desktop prototype，不是 formal installer，不做 code signing、auto update、telemetry upload 或正式发布包。

## 高风险问题

未发现。

没有发现 `.env`、数据库、日志、缓存、frontend build outputs 或 desktop build outputs 被 git 跟踪；也未发现真实 API key、前端 secret 注入、crash report secret 泄露或 health check secret 泄露。

## 中风险问题

1. v1.7 Backup / Restore runtime API 尚未形成完整实现。
   当前已有 desktop policy、文档和测试覆盖默认排除、secret redaction、dry-run/confirmation 要求，但完整 backup/restore API/CLI 不是当前代码中的完整运行时服务。最终验收时不能把 policy 覆盖夸大成完整 restore runtime。

2. v1.7 Log Viewer runtime API 尚未形成完整实现。
   当前有 `DesktopStudioPolicy.redact_log` 和日志本地化边界，但未看到完整 `LogViewerService` / `/debug/logs` runtime。Log Viewer 的“只读 logs/ + 防路径穿越”仍需后续实现或验收确认。

3. frontend build artifact 未在本次审查中重新生成。
   代码层和 policy 层显示前端只使用 `VITE_API_BASE_URL`，但若最终 release 要发布 `frontend/dist`，仍应对实际 build output 进行 artifact scan。

## 小问题

1. `DesktopStudioPolicy.forbidden_bundle_dirs` 包含 `desktop-build`，而 `.gitignore` 同时使用 `desktop_build/` 和 `desktop-build/`。
   当前 `.gitignore` 覆盖足够，但 bundle policy 可以同步加入 `desktop_build`，减少命名差异风险。

2. `LocalConfigManager.check_provider_config` 在普通 config issues 中可能使用 `LLM_API_KEY` 作为 `safe_field`。
   这不是 secret value，但从最严格 UI 隐私口径看，可以像 health check 一样归一为 `provider_config`。

3. `LOCAL_LLM_BASE_URL` 通过启动脚本传给后端进程。
   它不是 API key，但文档应提醒不要把 credential 放进 URL，以免本地进程列表或诊断输出扩大暴露面。

4. zip slip / executable 拒绝主要来自既有 package/module import 系统。
   v1.7 自己的 Backup / Restore 完整实现如果后续补齐，必须复用同等检查。

## 修复建议

1. 在 `DesktopStudioPolicy.forbidden_bundle_dirs` 中补齐 `desktop_build`、`release`、`crash-reports`、`backups`，与 `.gitignore` 保持完全一致。
2. 将普通 config issue 的 `safe_field` 从具体 secret env 名归一为 `provider_config`。
3. 补齐或验收 `LogViewerService` 时强制只读 `logs/`、拒绝路径穿越，并复用 crash/log redaction。
4. 补齐或验收 Backup / Restore runtime 时强制 zip slip 检查、executable rejection、checksum、dry-run、conflict detection 和 explicit confirmation。
5. 在 v1.7 最终冻结前对实际 `frontend/dist` 和 desktop packaging output 执行 secret/artifact 扫描。

## 是否阻塞 v1.7 release

不阻塞 v1.7 release。

当前没有高风险 release blocker。中风险项主要是 v1.7 的 Log Viewer 与 Backup / Restore 完整 runtime 尚需在最终验收时如实说明或补齐；现有 security policy、文档和测试已覆盖关键安全边界，但不能把未完整落地的 runtime 描述成已完成能力。
