# v1.6 Security / Module / Import Audit

## Scope

This audit covers the v1.6 Advanced Gameplay Modules security surface:

- gameplay module import/export
- gameplay module manifest permissions
- declarative action mods
- module debug and quality APIs
- module package CLI behavior
- tracked sensitive files
- API key and secret leakage checks
- real-provider and test safety boundaries

It does not modify business code.

## Verification Date

2026-05-20

## Verification Commands

```powershell
rg "zip slip|executable|FORBIDDEN_CODE_SUFFIXES|\.env|api_key|sk-|secret|checksum|archive|ZipFile|path traversal|resolve\(|parents|access_network|execute_code|access_filesystem|call_llm" backend\app\engine\gameplay_module_packages.py backend\app\engine\gameplay_module_loader.py backend\app\engine\action_mod_validator.py backend\app\tools\module_package.py backend\app\main.py backend\tests\test_gameplay_module_packages.py backend\tests\test_gameplay_module_loader.py backend\tests\test_action_mod_authoring_api.py frontend\src
git ls-files .env *.db *.sqlite *.sqlite3 *.log data frontend/dist node_modules desktop dist build .cache __pycache__
rg "sk-[A-Za-z0-9]{20,}|OPENAI_API_KEY|LLM_API_KEY|api_key\s*[:=]|secret\s*[:=]" -g "!frontend/node_modules/**" -g "!node_modules/**" -g "!frontend/dist/**" -g "!*.pyc" .
rg "require_debug_api|require_authoring_api|quality/modules|/modules/export|import-dry-run|action-mods|debug/modules" backend\app\main.py -n
```

## 已通过项目

1. **module import 禁止 zip slip**
   - `backend/app/engine/gameplay_module_packages.py` 使用 archive name 校验拒绝绝对路径、`..` 路径段和解压后越界路径。
   - `_extract_package` 在写入临时目录前再次解析目标路径并确认目标仍位于临时根目录下。
   - 测试覆盖 zip slip 拒绝路径。

2. **module import 拒绝可执行文件**
   - module package 层和 module loader 层都使用 `FORBIDDEN_CODE_SUFFIXES` 拒绝脚本/可执行文件。
   - `backend/tests/test_gameplay_module_packages.py` 与 loader 相关测试覆盖 executable rejection。

3. **module manifest execute_code 默认拒绝**
   - `GameplayModuleManifest.permissions` 默认最小权限。
   - `execute_code`、`access_network`、`access_filesystem`、`call_llm`、`modify_game_state_directly` 等危险权限为 `true` 时会被 validation 拒绝。

4. **module 不能读取 `.env` / API key**
   - v1.6 action mod 是声明式定义，不执行模块代码。
   - package export/import 拒绝 `.env`、`secrets.yaml`、`secrets.json`、数据库和日志类文件。
   - export 过程扫描 secret-like token，包括 `api_key`、`secret_key`、`private_key`、`bearer `、`sk-`。

5. **module 不能访问网络**
   - manifest `access_network` 和 `call_llm` 默认关闭，并在 validation 中拒绝启用。
   - declarative action handler、DSL、module import/export 和 quality gate 不进行网络调用。

6. **module 不能访问 root 外文件**
   - module discovery/load 使用模块根目录和路径解析校验。
   - package import 解压到临时目录，并拒绝 archive 内路径穿越。
   - import apply 只能写入受控 modules root 下的目标模块目录。

7. **module debug API 受 `ENABLE_DEBUG_API` 控制**
   - `/debug/modules`
   - `/debug/modules/{module_id}`
   - `/debug/modules/{module_id}/actions/{action_id}/dry-run`
   - 以上接口均调用 `require_debug_api`。

8. **module quality API 受本地配置控制**
   - `/quality/modules/{module_id}/gate/run` 调用 `require_quality_api`。
   - 当前 quality API 由本地 eval/playtest/perf/debug 配置打开，不默认暴露为普通玩家 API。

9. **module package export 不包含 API key**
   - export 打包前扫描文件名和文本内容中的 secret-like token。
   - 发现疑似 API key 时返回 `contains_api_key=true` 并清空 archive payload。
   - 测试覆盖 safe export 不包含 `api_key` / `sk-`。

10. **module package export 不包含数据库/logs/cache**
    - export/import 校验拒绝 `.db`、`.sqlite`、`.sqlite3`、`.log` 文件。
    - git tracked file 检查未发现 `.env`、数据库、日志、缓存、`node_modules`、`frontend/dist` 或 desktop build outputs 被跟踪。

11. **Action Mod Authoring UI 不提供任意代码编辑器**
    - UI/API 面向 declarative action fields、preconditions、checks、effects、visibility policy。
    - 不暴露 `execute_code` 编辑能力。
    - validate/export API 受 `ENABLE_AUTHORING_API` 控制，且不执行 action。

12. **CLI 不输出 secrets**
    - `backend/app/tools/module_package.py` 在 JSON 输出时剥离 `archive_base64`。
    - CLI 输出导入/校验报告，不打印 API key、raw env 或 package binary payload。

13. **frontend 不存储 API key**
    - 前端只展示 safe summary / redacted status，例如 `api_key_configured`、`contains_api_key`。
    - 未发现将 API key 写入 local storage、导出包或普通 UI 的路径。

14. **`.env` 未被 git 跟踪**
    - `git ls-files` 检查未发现 `.env` 被跟踪或暂存。

15. **数据库、日志、缓存、构建产物未被 git 跟踪**
    - `git ls-files` 检查未发现数据库、日志、缓存、`node_modules`、`frontend/dist`、desktop build output 被跟踪。

16. **未发现真实 `sk-...` key**
    - secret 扫描仅发现文档说明、配置名和测试假 key。
    - 测试假 key 采用 `sk-test-*`、`sk-real-looking-secret` 等上下文明确的 redaction fixture。

17. **provider factory 缺配置时清晰失败**
    - 既有 provider factory/provider tests 覆盖 OpenAI / local_http 缺配置失败。
    - v1.6 module 系统不新增绕过 provider factory 的路径。

18. **测试不调用真实 API**
    - v1.6 module tests 使用 direct handler、mock/fake/local_stub 风格路径。
    - 未发现 module tests 要求真实 OpenAI 或真实本地模型服务。

## 高风险问题

本次 security / module / import 专项审查未发现新的高风险安全问题。

注意：`docs/V1_6_VISIBILITY_GAMEPLAY_MOD_AUDIT.md` 已记录一个独立 visibility 风险：`ActionEffectType.ADD_FACT_DISCOVERY` 可将任意 `fact_id` 编译为 `player_visible_facts` delta，若被不可信 action mod 使用，可能暴露 hidden fact。该问题属于 visibility/gameplay 边界，不是 package import / code execution 安全问题，但若未修复或未限定为可信内容，仍可能阻塞 v1.6 release。

## 中风险问题

1. **secret 扫描仍是启发式**
   - 当前 export 扫描能拦截常见 token 和 `sk-` 形态，但不能证明所有二进制或非常规 secret 格式都会被识别。
   - 由于模块包设计为 declarative/docs/test content，不应包含二进制私密材料；建议继续收紧 allowlist。

2. **quality API gating 较宽**
   - `require_quality_api` 由 eval/playtest/perf/debug 等本地开关之一启用。
   - 这符合本地工作室定位，但不如专用 `ENABLE_QUALITY_API` 精确。建议在文档中明确，或后续增加独立开关。

3. **CLI 可以读取用户显式传入的本地 archive**
   - 这是 CLI 的预期能力，不属于路径穿越。
   - 风险在于用户传入错误文件时 CLI 会尝试读取并校验；当前输出不会打印 secrets，import dry-run 不写模块目录。

## 小问题

1. 前端类型和 UI 文案中存在 `api_key_configured`、`contains_api_key` 等字段名，属于安全状态字段，不包含 key 值。
2. 文档和测试中存在多个 fake key / redaction fixture，release 前 secret 扫描会产生噪音；建议保留固定命名约定以便人工区分。
3. module package export 对 `.cache` 目录不是显式按名称拒绝，但数据库/log/sensitive/executable/secret-like content 会被拦截；建议后续加入更严格的目录 allowlist。

## 修复建议

1. 保持当前 zip slip、executable rejection、permission rejection、checksum validation 和 quality gate 阻断测试。
2. 后续可为 module package 增加更严格的内容 allowlist，例如只允许 manifest、actions、rule configs、quality tests、docs 和 example content。
3. 后续可扩展敏感文件拒绝列表，覆盖 `.pem`、`.key`、`.p12`、`.crt`、`.bak`、`.cache` 等。
4. 考虑增加独立 `ENABLE_QUALITY_API`，让 module quality API gating 更直观。
5. 保持 CLI 默认不打印 archive payload，不输出 raw env、API key 或 hidden/debug text。

## 是否阻塞 v1.6 release

从 security / module / import 专项审查角度：**不阻塞 v1.6 release**。

但 v1.6 release 仍需结合 visibility/gameplay/mod audit 的 hidden fact discovery 风险一起判断。如果该 visibility 风险尚未修复或未被明确限定为可信模块内容，建议在最终 release gate 中继续将其作为独立阻塞项跟踪。
