import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";
import {
  CostLatencyGroupSummary,
  ModelUsageRecord,
  ModelUsageSummary,
  ProviderCapabilityCatalog,
  ProviderConnectionStatus,
  ProviderModelCapabilityMatrix,
  ProviderProfileDraft,
  ProviderProfileSummary,
  ProviderRoutingConfig,
  ProviderRoutingRule,
  ProviderRoutingUseCase,
  ProviderSetupChecklistReport,
  ProjectProviderModelAssignmentSummary,
  StudioConfigSummary,
  StructuredOutputReliabilityReport,
  LocalModelDiagnosticReport,
  LocalConfigIssue,
  LocalConfigSummary,
  LocalEnvTemplateResponse,
  PromptDiffReport,
  PromptRegressionReport,
  ProjectWorkspace,
  ProviderBenchmarkReport,
  createProjectProvider,
  fetchModelUsageSummary,
  fetchProjectProviderCapabilityMatrix,
  fetchProjectProviderModels,
  fetchProjectProviderModelAssignments,
  fetchProjectProviderSetupChecklist,
  fetchProjectProviderStatus,
  fetchProjectProviderUsageByMode,
  fetchProjectProviderUsageByProvider,
  fetchProjectProviderUsageRecent,
  fetchProjectProviderUsageSummary,
  fetchProjectProviders,
  fetchProviderCapabilities,
  fetchRecentModelUsage,
  getErrorMessageSafe,
  patchProjectProviderModels,
  ProviderModelFetchReport,
  ProviderModelPatchItem,
  reviewPromptDiff,
  runLocalModelDiagnostics,
  runPromptRegressionSuite,
  runProviderBenchmark,
  runStructuredOutputReliability,
  saveProjectProviderModelAssignments,
  syncProjectProviderModels,
  testProjectProviderConnection,
  validateProjectProvider,
  validateProjectProviderModelAssignments
} from "./api";
import { buildSafeSearchIndex, safeSearchMatches, useDebouncedValue } from "./filterUtils";
import {
  getSafeApiCacheStatuses,
  markSafeApiCacheFailed,
  readSafeApiCache,
  SafeApiCacheStatus,
  writeSafeApiCache
} from "./safeApiCache";

const PROVIDER_LEGACY_STATIC_REGRESSION_TOKENS = [
  "raw provider responses are never rendered"
];
void PROVIDER_LEGACY_STATIC_REGRESSION_TOKENS;

type PromptLabPageProps = {
  summary: StudioConfigSummary | null;
  configError: string;
  projectId: string;
  onSelectPromptProfile: (profileId: string) => void;
};

type ProviderConnectivityStatus =
  | "unconfigured"
  | "configured_not_tested"
  | "connected"
  | "disconnected"
  | "missing_secret"
  | "invalid_base_url"
  | "auth_failed"
  | "model_list_failed"
  | "unsupported_model_list"
  | "timeout";

type ProviderSecretInputMode = "transient" | "api_key_env" | "secret_ref" | "local_secret_ref" | "none";
type ProviderWizardStep = "type" | "secret" | "test" | "models" | "assignment" | "save";
type ProviderModelCapabilityFilter = "all" | "supports_text" | "supports_json" | "supports_streaming" | "supports_tools";
type ProviderModelEnabledFilter = "all" | "enabled" | "disabled";
type ProviderCapabilityMatrixFilter = "all" | "supports_text" | "supports_json" | "supports_streaming" | "supports_tools";

type ProviderModelListRow = {
  id: string;
  providerId: string;
  providerName: string;
  providerType: string;
  modelId: string;
  displayName: string;
  enabled: boolean;
  supportsText: boolean;
  supportsJson: boolean;
  supportsStreaming: boolean;
  supportsTools: boolean;
  recommendedUseCases: string[];
  warnings: string[];
};

type ProviderConnectivityRow = {
  providerId: string;
  displayName: string;
  providerType: string;
  connectionStatus: ProviderConnectivityStatus;
  modelCount: number;
  lastTestedTime: string;
  cacheState: string;
  stale: boolean;
  latencyMs?: number;
  latencyLabel: string;
  safeErrorType: string;
  allowedModes: string[];
  defaultModel: string;
  warnings: string[];
};

type SlowProviderWarning = {
  id: string;
  kind: "high_latency" | "repeated_timeout" | "model_list_slow" | "high_error_rate";
  severity: "warning" | "failed";
  source: string;
  safeSummary: string;
  suggestedActions: string[];
};

type ProviderCapabilityMatrixSafeRow = {
  id: string;
  providerId: string;
  providerName: string;
  modelId: string;
  supportsText: boolean;
  supportsJson: boolean;
  supportsStreaming: boolean;
  supportsTools: boolean;
  recommendedUseCases: string[];
  warnings: string[];
  disabledReasons: string[];
};

type ProviderCapabilityMatrixSafeSummary = {
  generatedAt: string;
  rowCount: number;
  providerCount: number;
  warningCount: number;
  blockerCount: number;
  providers: Array<{ providerId: string; providerName: string; rowCount: number; warningCount: number; blockerCount: number }>;
  useCases: string[];
  rows: ProviderCapabilityMatrixSafeRow[];
};

type ProviderModelListSafeCacheSummary = {
  project_id: string;
  provider_count: number;
  model_count: number;
  matrix_row_count: number;
  generated_at: string;
  providers: Array<{
    provider_profile_id: string;
    display_name: string;
    provider_type: string;
    model_count: number;
    enabled: boolean;
  }>;
};

const SAFE_API_CACHE_PROVIDER_TTL_MS = 3 * 60 * 1000;
const PROVIDER_HIGH_LATENCY_MS = 8000;
const PROVIDER_AVERAGE_LATENCY_WARNING_MS = 4000;
const PROVIDER_HIGH_ERROR_RATE = 0.2;
const PROVIDER_TIMEOUT_REPEAT_COUNT = 2;
const PROVIDER_MODEL_PAGE_SIZE = 40;
const PROVIDER_SETUP_WIZARD_STEPS: Array<{ id: ProviderWizardStep; label: string; detail: string }> = [
  { id: "type", label: "选择模型服务", detail: "选择 OpenAI、兼容 API、中转站、本地模型、自定义 API 或测试 Mock。" },
  { id: "secret", label: "密钥来源", detail: "选择临时 Key、环境变量、secret_ref、local_secret_ref 或无需密钥。" },
  { id: "test", label: "测试连接", detail: "只有点击按钮并确认时才会连接真实 Provider；测试默认仍可走 fake。" },
  { id: "models", label: "读取模型", detail: "读取模型列表或手动添加 model_id，不显示 raw provider response。" },
  { id: "assignment", label: "分配模型", detail: "按 Novel、Tavern、World、Cross-Mode、Quality 分配模型。" },
  { id: "save", label: "保存配置", detail: "只保存安全 profile metadata，不保存明文 API Key。" }
];
const PROVIDER_TYPE_OPTIONS: Array<{ value: string; label: string; detail: string; requiresSecret: boolean }> = [
  { value: "openai", label: "OpenAI", detail: "官方 OpenAI API。Base URL 可留空或使用兼容 /v1 地址。", requiresSecret: true },
  { value: "openai_compatible", label: "OpenAI-compatible", detail: "兼容 OpenAI /v1/models 与 chat/completions 的本地或第三方端点。", requiresSecret: true },
  { value: "relay", label: "中转站 / Relay", detail: "仅表示兼容 API 的 base URL 配置，不是 API 转售服务。", requiresSecret: true },
  { value: "local_http", label: "本地模型服务 / local_http", detail: "本机模型服务，可不需要 API Key；仍然只在手动点击时连接。", requiresSecret: false },
  { value: "custom", label: "自定义 API", detail: "使用自定义 base URL 与可选模型列表端点。", requiresSecret: true },
  { value: "mock", label: "Mock / 测试", detail: "测试与 CI 使用的安全假 Provider，不真实联网。", requiresSecret: false },
  { value: "local_stub", label: "Local Stub / 本地假模型", detail: "本地 dry-run 默认值，不真实联网。", requiresSecret: false }
];
const SLOW_PROVIDER_SAFE_ACTIONS = [
  "check base URL",
  "check local model service",
  "check provider status",
  "use another model/fallback",
  "increase timeout cautiously"
];

const PROVIDER_MODEL_ASSIGNMENT_USE_CASES: Array<{ value: ProviderRoutingUseCase; label: string }> = [
  { value: "novel_draft", label: "小说草稿" },
  { value: "novel_rewrite", label: "小说改写" },
  { value: "tavern_reply", label: "Tavern 回复" },
  { value: "multi_npc_reply", label: "多 NPC 场景" },
  { value: "world_intent_parse", label: "世界输入解析" },
  { value: "world_narration", label: "世界叙事渲染" },
  { value: "cross_mode_draft", label: "Cross-Mode 草稿" },
  { value: "memory_summary", label: "记忆摘要" },
  { value: "quality_eval", label: "质量检查" },
  { value: "cheap_summary", label: "低成本摘要" }
];

export function PromptLabPage({
  summary,
  configError,
  projectId,
  onSelectPromptProfile
}: PromptLabPageProps) {
  const [capabilities, setCapabilities] = useState<ProviderCapabilityCatalog | null>(null);
  const [benchmarkReport, setBenchmarkReport] = useState<ProviderBenchmarkReport | null>(null);
  const [structuredReport, setStructuredReport] = useState<StructuredOutputReliabilityReport | null>(null);
  const [regressionReport, setRegressionReport] = useState<PromptRegressionReport | null>(null);
  const [diagnosticReport, setDiagnosticReport] = useState<LocalModelDiagnosticReport | null>(null);
  const [usageSummary, setUsageSummary] = useState<ModelUsageSummary | null>(null);
  const [recentUsage, setRecentUsage] = useState<ModelUsageRecord[]>([]);
  const [projectUsageSummary, setProjectUsageSummary] = useState<ModelUsageSummary | null>(null);
  const [projectRecentUsage, setProjectRecentUsage] = useState<ModelUsageRecord[]>([]);
  const [usageByMode, setUsageByMode] = useState<CostLatencyGroupSummary[]>([]);
  const [usageByProvider, setUsageByProvider] = useState<CostLatencyGroupSummary[]>([]);
  const [usageRange, setUsageRange] = useState<number | undefined>(undefined);
  const [providerProfiles, setProviderProfiles] = useState<ProviderProfileSummary[]>([]);
  const [providerCapabilityMatrix, setProviderCapabilityMatrix] = useState<ProviderModelCapabilityMatrix | null>(null);
  const [providerStatus, setProviderStatus] = useState<Record<string, unknown> | null>(null);
  const [providerStatusById, setProviderStatusById] = useState<Record<string, Record<string, unknown>>>({});
  const [providerLastTestedById, setProviderLastTestedById] = useState<Record<string, string>>({});
  const [providerMetadataLoading, setProviderMetadataLoading] = useState(false);
  const [providerSafeCacheStatuses, setProviderSafeCacheStatuses] = useState<SafeApiCacheStatus[]>(() => getSafeApiCacheStatuses().filter((status) => status.scope === "provider"));
  const [providerSetupChecklist, setProviderSetupChecklist] = useState<ProviderSetupChecklistReport | null>(null);
  const [providerSetupChecklistError, setProviderSetupChecklistError] = useState("");
  const [modelAssignmentOpen, setModelAssignmentOpen] = useState(false);
  const [providerValidation, setProviderValidation] = useState("");
  const [providerDraft, setProviderDraft] = useState<ProviderProfileDraft>({
    provider_profile_id: "local_stub",
    display_name: "Local Stub",
    provider_type: "local_stub",
    api_key_env: "",
    secret_ref: "",
    model_profiles: [{ model_id: "local_stub", display_name: "Local Stub", supports_json: true, supports_streaming: false }],
    allowed_modes: ["novel", "tavern", "world", "cross_mode", "quality"],
    default_timeout_seconds: 30,
    enabled: true,
    requires_api_key: false
  });
  const [diffReport, setDiffReport] = useState<PromptDiffReport | null>(null);
  const [labError, setLabError] = useState("");

  async function runLabAction(action: () => Promise<void>) {
    setLabError("");
    try {
      await action();
    } catch (err) {
      setLabError(toErrorMessage(err));
    }
  }

  function syncProviderSafeCacheStatuses() {
    setProviderSafeCacheStatuses(getSafeApiCacheStatuses().filter((status) => status.scope === "provider"));
  }

  async function loadProviderSetupChecklist() {
    setProviderSetupChecklistError("");
    try {
      setProviderSetupChecklist(await fetchProjectProviderSetupChecklist(projectId));
    } catch (error) {
      setProviderSetupChecklistError(toErrorMessage(error));
    }
  }

  function jumpToProviderChecklistTarget(target: string) {
    if (target === "assignment") {
      setModelAssignmentOpen(true);
    }
    const selector =
      target === "provider_setup" || target === "privacy"
        ? ".provider-profile-form"
        : target === "assignment"
          ? ".model-assignment-panel"
          : ".provider-connectivity-dashboard";
    window.setTimeout(() => {
      document.querySelector(selector)?.scrollIntoView({ behavior: motionSafeScrollBehavior(), block: "start" });
    }, 0);
  }

  async function loadProjectUsage() {
    const [summaryResult, recentResult, byModeResult, byProviderResult] = await Promise.all([
      fetchProjectProviderUsageSummary(projectId, usageRange),
      fetchProjectProviderUsageRecent(projectId, 12, usageRange),
      fetchProjectProviderUsageByMode(projectId, usageRange),
      fetchProjectProviderUsageByProvider(projectId, usageRange)
    ]);
    setProjectUsageSummary(summaryResult);
    setProjectRecentUsage(recentResult.records);
    setUsageByMode(byModeResult.by_mode);
    setUsageByProvider(byProviderResult.by_provider);
  }

  async function loadProviderProfiles(force = false) {
    const cacheKey = providerModelListCacheKey(projectId);
    const cached = readSafeApiCache<ProviderModelListSafeCacheSummary>(cacheKey);
    if (!force && cached && !cached.stale && providerProfiles.length > 0 && providerCapabilityMatrix) {
      syncProviderSafeCacheStatuses();
      return;
    }
    setProviderMetadataLoading(true);
    try {
      const [profilesResult, matrixResult] = await Promise.all([
        fetchProjectProviders(projectId),
        fetchProjectProviderCapabilityMatrix(projectId)
      ]);
      setProviderProfiles(profilesResult.providers);
      setProviderCapabilityMatrix(matrixResult.matrix);
      void loadProviderSetupChecklist();
      const cacheSummary = buildProviderModelListSafeCacheSummary(projectId, profilesResult.providers, matrixResult.matrix);
      writeSafeApiCache(cacheKey, "Provider model list safe summary", "provider", cacheSummary, {
        staleAfterMs: SAFE_API_CACHE_PROVIDER_TTL_MS,
        summary: `${cacheSummary.provider_count} provider(s), ${cacheSummary.model_count} safe ModelProfile row(s).`,
        itemCount: cacheSummary.model_count
      });
      syncProviderSafeCacheStatuses();
    } catch (err) {
      markSafeApiCacheFailed(cacheKey, "Provider model list safe summary", "provider", err);
      syncProviderSafeCacheStatuses();
      throw err;
    } finally {
      setProviderMetadataLoading(false);
    }
  }

  function cleanProviderDraft(draft: ProviderProfileDraft): ProviderProfileDraft {
    const cleaned: ProviderProfileDraft = {
      ...draft,
      provider_profile_id: draft.provider_profile_id.trim(),
      display_name: draft.display_name.trim() || draft.provider_profile_id.trim(),
      provider_type: draft.provider_type.trim(),
      base_url: draft.base_url?.trim() || null,
      base_url_env: draft.base_url_env?.trim() || null,
      api_key_env: draft.api_key_env?.trim() || null,
      secret_ref: draft.secret_ref?.trim() || null,
      local_secret_ref: draft.local_secret_ref?.trim() || null,
      allowed_modes: draft.allowed_modes ?? [],
      model_profiles: draft.model_profiles
        .filter((model) => model.model_id.trim())
        .map((model) => ({
          ...model,
          model_id: model.model_id.trim(),
          display_name: model.display_name?.trim() || model.model_id.trim(),
          recommended_use_cases: model.recommended_use_cases ?? []
        }))
    };
    return cleaned;
  }

  async function saveProviderDraftProfile(draft: ProviderProfileDraft = providerDraft) {
    const cleaned = cleanProviderDraft(draft);
    const created = await createProjectProvider(projectId, cleaned);
    setProviderProfiles((current) => [...current.filter((item) => item.provider_profile_id !== created.provider.provider_profile_id), created.provider]);
    setProviderValidation("Provider 配置已保存；明文 API Key 未写入 project，只会由后端从 env、secret_ref 或 local_secret_ref 解析。");
    void loadProviderSetupChecklist();
    return created.provider;
  }

  async function saveProviderProfile(event: FormEvent) {
    event.preventDefault();
    await saveProviderDraftProfile(providerDraft);
  }

  async function validateProvider(profileId: string) {
    const result = await validateProjectProvider(projectId, profileId);
    setProviderValidation(result.ok ? "Provider profile validates." : `Provider profile failed validation: ${result.warnings.join(", ")}`);
    setProviderLastTestedById((current) => ({ ...current, [profileId]: new Date().toISOString() }));
  }

  async function loadProviderStatus(profileId: string, force = false) {
    const cacheKey = providerStatusCacheKey(projectId, profileId);
    const cached = readSafeApiCache<Record<string, unknown>>(cacheKey);
    if (!force && cached && !cached.stale) {
      setProviderStatus(cached.value);
      setProviderStatusById((current) => ({ ...current, [profileId]: cached.value }));
      if (typeof cached.value.tested_at === "string") {
        setProviderLastTestedById((current) => ({ ...current, [profileId]: cached.value.tested_at as string }));
      }
      syncProviderSafeCacheStatuses();
      return;
    }
    try {
      const result = await fetchProjectProviderStatus(projectId, profileId);
      const statusPayload = (result.connection_cache ?? (typeof result.status === "string" ? { status: result.status } : result.status)) as Record<string, unknown>;
      const safeCacheValue = buildProviderStatusSafeCacheValue(profileId, statusPayload);
      setProviderStatus(safeCacheValue);
      setProviderStatusById((current) => ({ ...current, [profileId]: safeCacheValue }));
      if (typeof safeCacheValue.tested_at === "string") {
        setProviderLastTestedById((current) => ({ ...current, [profileId]: safeCacheValue.tested_at as string }));
      }
      writeSafeApiCache(cacheKey, `Provider status safe summary: ${profileId}`, "provider", safeCacheValue, {
        staleAfterMs: SAFE_API_CACHE_PROVIDER_TTL_MS,
        summary: `${profileId} status ${safeCacheValue.status}; manual refresh available.`,
        itemCount: typeof safeCacheValue.model_count === "number" ? safeCacheValue.model_count : undefined
      });
      syncProviderSafeCacheStatuses();
      void loadProviderSetupChecklist();
    } catch (err) {
      markSafeApiCacheFailed(cacheKey, `Provider status safe summary: ${profileId}`, "provider", err);
      syncProviderSafeCacheStatuses();
      throw err;
    }
  }

  async function refreshProviderConnection(profileId: string) {
    const cacheKey = providerStatusCacheKey(projectId, profileId);
    try {
      const status = await testProjectProviderConnection(projectId, profileId);
      const cacheView = buildProviderStatusSafeCacheValue(profileId, status as unknown as Record<string, unknown>);
      setProviderStatus(cacheView);
      setProviderStatusById((current) => ({ ...current, [profileId]: cacheView }));
      setProviderLastTestedById((current) => ({ ...current, [profileId]: status.tested_at }));
      writeSafeApiCache(cacheKey, `Provider status safe summary: ${profileId}`, "provider", cacheView, {
        staleAfterMs: SAFE_API_CACHE_PROVIDER_TTL_MS,
        summary: `${profileId} connection ${status.status}; redaction applied ${status.redaction_applied ? "yes" : "no"}.`
      });
      syncProviderSafeCacheStatuses();
      void loadProviderSetupChecklist();
    } catch (err) {
      markSafeApiCacheFailed(cacheKey, `Provider status safe summary: ${profileId}`, "provider", err);
      syncProviderSafeCacheStatuses();
      throw err;
    }
  }

  function updateProviderConnectionStatus(profileId: string, status: ProviderConnectionStatus) {
    const cacheKey = providerStatusCacheKey(projectId, profileId);
    const cacheView = buildProviderStatusSafeCacheValue(profileId, status as unknown as Record<string, unknown>);
    setProviderStatus(cacheView);
    setProviderStatusById((current) => ({ ...current, [profileId]: cacheView }));
    setProviderLastTestedById((current) => ({ ...current, [profileId]: status.tested_at }));
    writeSafeApiCache(cacheKey, `Provider status safe summary: ${profileId}`, "provider", cacheView, {
      staleAfterMs: SAFE_API_CACHE_PROVIDER_TTL_MS,
      summary: `${profileId} connection ${status.status}; redaction applied ${status.redaction_applied ? "yes" : "no"}.`
    });
    syncProviderSafeCacheStatuses();
    void loadProviderSetupChecklist();
  }

  const profiles = summary?.prompt_profiles ?? [];
  const leftProfile = profiles[0] ? { id: profiles[0].id, hidden_fact_policy: "deny", state_modification_policy: "deny" } : {};
  const rightProfile = profiles[1] ? { id: profiles[1].id, hidden_fact_policy: "deny", state_modification_policy: "deny" } : leftProfile;

  useEffect(() => {
    void loadProviderSetupChecklist();
  }, [projectId]);

  return (
    <section className="studio-section" data-route-chunk="provider-ui">
      <div className="authoring-pane-header">
        <div>
          <h3>Prompt Lab / Provider Connectivity</h3>
          <p className="muted">Lazy-loaded local provider workbench. All summaries are redacted and local-only.</p>
        </div>
        <StatusBadge label={summary?.debug_api_enabled || summary?.performance_logging_enabled ? "Local APIs ready" : "API gated"} enabled={Boolean(summary?.debug_api_enabled || summary?.performance_logging_enabled)} />
      </div>
      <ErrorPanel message={labError || configError} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Provider" value={summary?.llm_provider ?? "unknown"}>
          <p>{summary?.provider_sends_prompts_off_machine ? "External provider requires explicit opt-in for real tests." : "No real provider call is made by default."}</p>
        </DashboardCard>
        <DashboardCard title="API Key" value={summary?.api_key_configured ? "configured" : "not shown"}>
          <p>Key values never render in Prompt Lab.</p>
        </DashboardCard>
        <DashboardCard title="Hidden Data" value="redacted">
          <p>Normal UI does not show hidden facts, raw env, raw prompts, or raw state deltas.</p>
        </DashboardCard>
      </div>

      <ProviderSetupWizard
        projectId={projectId}
        draft={providerDraft}
        profiles={providerProfiles}
        statusById={providerStatusById}
        onChange={setProviderDraft}
        onSaveProfile={(draft) => runLabAction(async () => {
          const saved = await saveProviderDraftProfile(draft);
          setProviderDraft({
            ...draft,
            provider_profile_id: saved.provider_profile_id,
            display_name: saved.display_name,
            provider_type: saved.provider_type,
            api_key_env: saved.api_key_env ?? "",
            secret_ref: saved.secret_ref ?? "",
            local_secret_ref: saved.local_secret_ref ?? "",
            model_profiles: saved.model_profiles.length ? saved.model_profiles : draft.model_profiles
          });
        })}
        onConnectionStatus={updateProviderConnectionStatus}
        onModelsChanged={() => void loadProviderProfiles(true)}
        onOpenAssignment={() => setModelAssignmentOpen(true)}
      />

      <ProviderCompleteSetupChecklist
        report={providerSetupChecklist}
        error={providerSetupChecklistError}
        onRefresh={() => void runLabAction(loadProviderSetupChecklist)}
        onJump={jumpToProviderChecklistTarget}
      />

      <ProviderConnectivityDashboard
        profiles={providerProfiles}
        matrix={providerCapabilityMatrix}
        statusById={providerStatusById}
        lastTestedById={providerLastTestedById}
        usageSummary={projectUsageSummary}
        recentUsage={projectRecentUsage}
        usageByProvider={usageByProvider}
        modelAssignmentOpen={modelAssignmentOpen}
        isLoading={providerMetadataLoading}
        cacheStatuses={providerSafeCacheStatuses}
        projectId={projectId}
        onChecklistRefresh={() => void loadProviderSetupChecklist()}
        onTestConnection={(profileId) => void runLabAction(async () => {
          await validateProvider(profileId);
          await refreshProviderConnection(profileId);
        })}
        onFetchModels={() => void runLabAction(() => loadProviderProfiles(false))}
        onRefreshModels={() => void runLabAction(() => loadProviderProfiles(true))}
        onOpenModelAssignment={() => setModelAssignmentOpen((open) => !open)}
        onOpenProviderSetup={() => {
          document.querySelector(".provider-profile-form")?.scrollIntoView({ behavior: motionSafeScrollBehavior(), block: "start" });
        }}
      />

      <section className="studio-section">
        <div className="authoring-pane-header">
          <div>
            <h4>Provider Capabilities</h4>
            <p className="muted">Declared provider/model metadata only; no network probe.</p>
          </div>
          <button type="button" onClick={() => void runLabAction(async () => setCapabilities(await fetchProviderCapabilities()))}>
            Load Capabilities
          </button>
        </div>
        {capabilities ? (
          <ItemList
            emptyText="No providers."
            items={capabilities.providers.map((provider) => (
              <span key={provider.provider_id}>
                {provider.provider_id}: json {provider.supports_json ? "yes" : "no"}, local {provider.local_only ? "yes" : "no"}
              </span>
            ))}
          />
        ) : (
          <p className="muted">Empty until loaded. API disabled states are shown as safe errors instead of exposing config.</p>
        )}
      </section>

      <section className="studio-section">
        <div className="authoring-pane-header">
          <div>
            <h4>Provider Profiles / Provider 配置</h4>
            <p className="muted">API Key 不在此处显示或保存；只使用环境变量、secret_ref 或 local_secret_ref。</p>
          </div>
          <button type="button" onClick={() => void runLabAction(() => loadProviderProfiles(true))}>
            载入配置 / Load Profiles
          </button>
        </div>
        <div className="mode-landing-grid">
          <FeatureCard title="openai" detail="Use api_key_env or secret_ref; the frontend never asks for plaintext keys." />
          <FeatureCard title="openai_compatible" detail="Use a local or trusted compatible endpoint with explicit base URL metadata." />
          <FeatureCard title="local_http" detail="Local model endpoint; capability warnings still apply." />
          <FeatureCard title="relay" detail="Relay-style profile metadata only. No API resale or specific relay support is implied." />
          <FeatureCard title="mock / local_stub" detail="Safe defaults for tests and local dry-runs." />
        </div>
        <ProviderProfileForm
          draft={providerDraft}
          validationMessage={providerValidation}
          onChange={setProviderDraft}
          onSubmit={(event) => void runLabAction(async () => saveProviderProfile(event))}
        />
        <ItemList
          emptyText="No provider profiles loaded."
          items={providerProfiles.map((profile) => (
            <span key={profile.provider_profile_id}>
              {profile.display_name} ({profile.provider_type}) - {profile.enabled ? "enabled" : "disabled"} - {profile.model_profiles.length} models
              <button type="button" onClick={() => void runLabAction(async () => validateProvider(profile.provider_profile_id))}>
                验证 / Validate
              </button>
              <button type="button" onClick={() => void runLabAction(async () => loadProviderStatus(profile.provider_profile_id, true))}>
                状态 / Status
              </button>
            </span>
          ))}
        />
        <ProviderCapabilityMatrixPanel matrix={providerCapabilityMatrix} profiles={providerProfiles} />
        {providerStatus ? <SafeJSON value={providerStatus} /> : null}
      </section>

      <section className="studio-section">
        <div className="authoring-pane-header">
          <div>
            <h4>Benchmarks / Reliability / Regression</h4>
            <p className="muted">Runs use fake/mock defaults. Real provider runs are not triggered here.</p>
          </div>
          <div className="button-row">
            <button type="button" onClick={() => void runLabAction(async () => setBenchmarkReport(await runProviderBenchmark(false)))}>
              Run Benchmark
            </button>
            <button type="button" onClick={() => void runLabAction(async () => setStructuredReport(await runStructuredOutputReliability(false)))}>
              Run JSON
            </button>
            <button type="button" onClick={() => void runLabAction(async () => setRegressionReport(await runPromptRegressionSuite()))}>
              Run Regression
            </button>
          </div>
        </div>
        <div className="studio-grid compact-dashboard-grid">
          <DashboardCard title="Benchmark" value={benchmarkReport?.run_id ? String(benchmarkReport.ok_cases) : "empty"}>
            <p>{benchmarkReport ? `${benchmarkReport.total_cases} cases, leak risks ${benchmarkReport.hidden_leak_risk_count}` : "No benchmark report loaded."}</p>
          </DashboardCard>
          <DashboardCard title="Structured JSON" value={structuredReport ? `${Math.round(structuredReport.schema_valid_rate * 100)}%` : "empty"}>
            <p>{structuredReport ? `${structuredReport.total_cases} cases, hidden policy ${structuredReport.hidden_policy_violation_rate}` : "No structured output report."}</p>
          </DashboardCard>
          <DashboardCard title="Regression" value={regressionReport?.pass_fail ?? "empty"}>
            <p>{regressionReport ? `${regressionReport.safety_blockers.length} safety blockers` : "No prompt regression report."}</p>
          </DashboardCard>
        </div>
      </section>

      <section className="studio-section">
        <div className="authoring-pane-header">
          <div>
            <h4>Prompt Diff / Local Diagnostics / Usage</h4>
            <p className="muted">Diff and diagnostics use redacted inputs. Usage records never include prompts or API keys.</p>
          </div>
          <div className="button-row">
            <button type="button" onClick={() => void runLabAction(async () => setDiffReport(await reviewPromptDiff(leftProfile, rightProfile)))}>
              Review Diff
            </button>
            <button type="button" onClick={() => void runLabAction(async () => setDiagnosticReport(await runLocalModelDiagnostics()))}>
              Diagnose Local
            </button>
            <button
              type="button"
              onClick={() =>
                void runLabAction(async () => {
                  setUsageSummary(await fetchModelUsageSummary());
                  setRecentUsage((await fetchRecentModelUsage(10)).records);
                })
              }
            >
              Load Usage
            </button>
          </div>
        </div>
        <div className="studio-grid compact-dashboard-grid">
          <DashboardCard title="Prompt Diff" value={diffReport ? String(diffReport.changed_sections.length) : "empty"}>
            <p>{diffReport ? `${diffReport.blockers.length} blockers, token delta ${diffReport.token_delta}` : "No diff report."}</p>
          </DashboardCard>
          <DashboardCard title="Local Diagnostics" value={diagnosticReport?.pass_fail ?? "empty"}>
            <p>{diagnosticReport ? `${diagnosticReport.provider_id}, base URL ${diagnosticReport.base_url_configured ? "configured" : "not needed"}` : "No diagnostic run."}</p>
          </DashboardCard>
          <DashboardCard title="Usage Calls" value={usageSummary ? String(usageSummary.total_calls) : "empty"}>
            <p>{usageSummary ? `p50 ${usageSummary.latency_p50_ms}ms / p95 ${usageSummary.latency_p95_ms}ms / cost ${usageSummary.total_cost_estimated}` : "Usage tracking may be disabled."}</p>
          </DashboardCard>
          <DashboardCard title="Error Rate" value={usageSummary ? `${Math.round(usageSummary.error_rate * 100)}%` : "empty"}>
            <p>{usageSummary ? `${usageSummary.failures} failures` : "No usage summary."}</p>
          </DashboardCard>
        </div>
        <ItemList
          emptyText="No recent usage records."
          items={recentUsage.map((record) => (
            <span key={record.usage_id}>
              {record.provider_id}/{record.model_id} {record.use_case}: {record.success ? "ok" : record.error_type ?? "failed"}
            </span>
          ))}
        />
      </section>

      <section className="studio-section">
        <ProviderUsageCostDashboard
          projectId={projectId}
          summary={projectUsageSummary}
          recent={projectRecentUsage}
          usageByMode={usageByMode}
          usageByProvider={usageByProvider}
          usageRange={usageRange}
          onRangeChange={setUsageRange}
          onLoad={() => void runLabAction(loadProjectUsage)}
        />
      </section>

      <PromptProfileSafeSettings
        summary={summary}
        onSelectPromptProfile={onSelectPromptProfile}
      />
    </section>
  );
}

const PROVIDER_CHECKLIST_JUMP_LABELS: Record<string, string> = {
  provider_setup: "Provider Setup",
  connection: "Connection Status",
  models: "Model List",
  assignment: "Model Assignment",
  privacy: "Privacy Boundary"
};

function ProviderCompleteSetupChecklist({
  report,
  error,
  onRefresh,
  onJump
}: {
  report: ProviderSetupChecklistReport | null;
  error: string;
  onRefresh: () => void;
  onJump: (target: string) => void;
}) {
  const overall = report?.overall_status ?? "missing";
  const renderedItems = report?.items ?? [];
  return (
    <section className="studio-section product-readiness-dashboard provider-setup-checklist" data-v37-provider-setup-checklist="safe-summary">
      <div className="authoring-pane-header">
        <div>
          <h4>Provider Complete Setup Checklist</h4>
          <p className="muted">Local-only readiness for Novel, Tavern, World, Cross-Mode, and Quality routing. API keys, one-time test keys, raw env, and provider raw responses are not rendered.</p>
        </div>
        <div className="button-row">
          <span className={`status-pill ${providerChecklistPillClass(overall)}`}>overall {overall}</span>
          <button type="button" onClick={onRefresh}>Refresh Checklist</button>
        </div>
      </div>
      <ErrorPanel message={error} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Pass" value={String(report?.pass_count ?? 0)}>
          <p>Provider setup items that are ready for local use.</p>
        </DashboardCard>
        <DashboardCard title="Warnings" value={String(report?.warning_count ?? 0)}>
          <p>Non-secret setup items needing review before daily use.</p>
        </DashboardCard>
        <DashboardCard title="Missing" value={String(report?.missing_count ?? 0)}>
          <p>Required local provider setup items that are absent.</p>
        </DashboardCard>
      </div>
      {report ? (
        <div className="product-readiness-list">
          {renderedItems.map((item) => (
            <article className={`product-readiness-item ${providerChecklistItemClass(item.status)}`} key={item.id}>
              <div className="product-readiness-heading">
                <h4>{item.label}</h4>
                <span className={`status-pill ${providerChecklistPillClass(item.status)}`}>{item.status}</span>
              </div>
              <p>{redactProviderChecklistText(item.safe_summary)}</p>
              <p className="muted">{redactProviderChecklistText(item.next_action)}</p>
              <button type="button" onClick={() => onJump(item.jump_target)}>
                Jump to {PROVIDER_CHECKLIST_JUMP_LABELS[item.jump_target] ?? "Provider Settings"}
              </button>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="Provider checklist not loaded." detail="Refresh the local checklist to inspect safe provider setup metadata. No real provider call is made." />
      )}
    </section>
  );
}

function ProviderSetupWizard({
  projectId,
  draft,
  profiles,
  statusById,
  onChange,
  onSaveProfile,
  onConnectionStatus,
  onModelsChanged,
  onOpenAssignment
}: {
  projectId: string;
  draft: ProviderProfileDraft;
  profiles: ProviderProfileSummary[];
  statusById: Record<string, Record<string, unknown>>;
  onChange: (draft: ProviderProfileDraft) => void;
  onSaveProfile: (draft: ProviderProfileDraft) => Promise<void> | void;
  onConnectionStatus: (profileId: string, status: ProviderConnectionStatus) => void;
  onModelsChanged: () => void;
  onOpenAssignment: () => void;
}) {
  const [currentStep, setCurrentStep] = useState(0);
  const [secretMode, setSecretMode] = useState<ProviderSecretInputMode>(() => inferSecretMode(draft));
  const [allowRealProviderCall, setAllowRealProviderCall] = useState(false);
  const [modelListEndpoint, setModelListEndpoint] = useState("");
  const [manualModelId, setManualModelId] = useState("");
  const [defaultModelId, setDefaultModelId] = useState(draft.model_profiles[0]?.model_id ?? "");
  const [lastStatus, setLastStatus] = useState<ProviderConnectivityStatus>(() => {
    const currentStatus = statusById[draft.provider_profile_id]?.status;
    return statusString(currentStatus ?? (profiles.length ? "configured_not_tested" : "unconfigured"));
  });
  const [fetchReport, setFetchReport] = useState<ProviderModelFetchReport | null>(null);
  const [message, setMessage] = useState("");
  const transientKeyRef = useRef<HTMLInputElement | null>(null);

  const providerType = PROVIDER_TYPE_OPTIONS.find((option) => option.value === draft.provider_type) ?? PROVIDER_TYPE_OPTIONS[0];
  const activeStep = PROVIDER_SETUP_WIZARD_STEPS[currentStep] ?? PROVIDER_SETUP_WIZARD_STEPS[0];
  const hasPersistedSecret = Boolean(draft.api_key_env || draft.secret_ref || draft.local_secret_ref);
  const availableModels = useMemo(
    () => Array.from(new Set([
      ...draft.model_profiles.map((model) => model.model_id).filter(Boolean),
      ...(fetchReport?.models ?? []).map((model) => model.model_id).filter(Boolean)
    ])),
    [draft.model_profiles, fetchReport]
  );

  useEffect(() => {
    setDefaultModelId(draft.model_profiles[0]?.model_id ?? "");
  }, [draft.model_profiles]);

  function updateDraft(next: Partial<ProviderProfileDraft>) {
    onChange({ ...draft, ...next });
  }

  function updateProviderType(providerTypeValue: string) {
    const option = PROVIDER_TYPE_OPTIONS.find((item) => item.value === providerTypeValue) ?? PROVIDER_TYPE_OPTIONS[0];
    const needsSecret = option.requiresSecret;
    const fallbackModel = providerTypeValue === "mock" ? "mock" : providerTypeValue === "local_stub" ? "local_stub" : draft.model_profiles[0]?.model_id || "";
    onChange({
      ...draft,
      provider_type: providerTypeValue,
      provider_profile_id: draft.provider_profile_id || providerTypeValue,
      display_name: draft.display_name || option.label,
      requires_api_key: needsSecret,
      model_profiles: draft.model_profiles.length ? draft.model_profiles : fallbackModel ? [{ model_id: fallbackModel, display_name: fallbackModel, supports_json: providerTypeValue !== "local_http", supports_streaming: false }] : []
    });
    if (!needsSecret && secretMode !== "none") {
      setSecretMode("none");
    }
  }

  function updateSecretMode(nextMode: ProviderSecretInputMode) {
    setSecretMode(nextMode);
    onChange({
      ...draft,
      api_key_env: nextMode === "api_key_env" ? draft.api_key_env || "OPENAI_API_KEY" : "",
      secret_ref: nextMode === "secret_ref" ? draft.secret_ref || "providers/main" : "",
      local_secret_ref: nextMode === "local_secret_ref" ? draft.local_secret_ref || "providers/main" : "",
      requires_api_key: nextMode !== "none" && providerType.requiresSecret
    });
  }

  function buildWizardPayload() {
    const transientKey = secretMode === "transient" ? transientKeyRef.current?.value.trim() || null : null;
    return {
      provider_profile_id: draft.provider_profile_id.trim() || null,
      provider_type: draft.provider_type,
      base_url: draft.base_url?.trim() || null,
      base_url_env: draft.base_url_env?.trim() || null,
      api_key_env: secretMode === "api_key_env" ? draft.api_key_env?.trim() || null : null,
      secret_ref: secretMode === "secret_ref" ? draft.secret_ref?.trim() || null : null,
      local_secret_ref: secretMode === "local_secret_ref" ? draft.local_secret_ref?.trim() || null : null,
      transient_api_key: transientKey,
      timeout_seconds: draft.default_timeout_seconds ?? 30,
      model_list_endpoint: modelListEndpoint.trim() || null,
      allow_real_connection: allowRealProviderCall,
      allow_real_provider: allowRealProviderCall
    };
  }

  function mergeFetchedModels(models: ProviderModelFetchReport["models"]) {
    if (!models.length) return;
    const byId = new Map(draft.model_profiles.map((model) => [model.model_id, model]));
    for (const model of models) {
      byId.set(model.model_id, {
        ...byId.get(model.model_id),
        model_id: model.model_id,
        display_name: model.display_name || model.model_id,
        supports_json: Boolean(model.supports_json),
        supports_streaming: Boolean(model.supports_streaming),
        recommended_use_cases: model.recommended_use_cases ?? []
      });
    }
    const merged = Array.from(byId.values());
    onChange({ ...draft, model_profiles: merged });
    if (!defaultModelId && merged[0]?.model_id) {
      setDefaultModelId(merged[0].model_id);
    }
  }

  function addManualModel() {
    const modelId = manualModelId.trim();
    if (!modelId) return;
    if (draft.model_profiles.some((model) => model.model_id === modelId)) {
      setMessage("这个 model_id 已经在列表中。");
      return;
    }
    onChange({
      ...draft,
      model_profiles: [
        ...draft.model_profiles,
        { model_id: modelId, display_name: modelId, supports_json: false, supports_streaming: false, recommended_use_cases: [] }
      ]
    });
    setManualModelId("");
    setMessage("已手动添加 model_id；保存配置后会写入 ModelProfile metadata。");
  }

  function selectDefaultModel(modelId: string) {
    setDefaultModelId(modelId);
    const existing = draft.model_profiles.find((model) => model.model_id === modelId) ?? { model_id: modelId, display_name: modelId, supports_json: false, supports_streaming: false, recommended_use_cases: [] };
    onChange({
      ...draft,
      model_profiles: [existing, ...draft.model_profiles.filter((model) => model.model_id !== modelId)]
    });
  }

  async function runWizardAction(action: () => Promise<void>) {
    setMessage("");
    try {
      await action();
    } catch (error) {
      setMessage(toErrorMessage(error));
    }
  }

  async function handleTestConnection() {
    const payload = buildWizardPayload();
    const result = await testProjectProviderConnection(projectId, draft.provider_profile_id, payload);
    const status = statusString(result.status);
    setLastStatus(status);
    onConnectionStatus(draft.provider_profile_id, result);
    setMessage(providerStatusToChinese(status, result.safe_message));
  }

  async function handleFetchModels(sync = false) {
    const payload = buildWizardPayload();
    const response = sync
      ? await syncProjectProviderModels(projectId, payload)
      : await fetchProjectProviderModels(projectId, payload);
    setFetchReport(response.report);
    mergeFetchedModels(response.report.models ?? []);
    if (sync) onModelsChanged();
    setMessage(providerStatusToChinese(statusString(response.report.status), response.report.safe_message));
  }

  return (
    <section className="studio-section provider-setup-wizard" data-testid="v37-provider-real-llm-wizard">
      <div className="authoring-pane-header">
        <div>
          <h4>模型服务设置向导</h4>
          <p className="muted">配置真实 LLM API 或本地模型服务。不允许保存明文 API Key 到 project、localStorage、sessionStorage、日志、备份、导出或诊断。</p>
        </div>
        <ProviderConnectionStatusBadge status={lastStatus} />
      </div>

      <div className="wizard-progress" aria-label="Provider 设置步骤">
        {PROVIDER_SETUP_WIZARD_STEPS.map((step, index) => (
          <button
            key={step.id}
            type="button"
            className={index === currentStep ? "active" : ""}
            onClick={() => setCurrentStep(index)}
          >
            {index + 1}. {step.label}
          </button>
        ))}
      </div>

      <article className="wizard-current-step">
        <strong>{activeStep.label}</strong>
        <p className="muted">{activeStep.detail}</p>
      </article>

      <div className="studio-grid two-column-grid">
        <SectionCard title="1. 模型服务类型" description={providerType.detail}>
          <div className="form-grid">
            <label>
              服务类型
              <select value={draft.provider_type} onChange={(event) => updateProviderType(event.target.value)}>
                {PROVIDER_TYPE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <label>
              配置 ID
              <input value={draft.provider_profile_id} onChange={(event) => updateDraft({ provider_profile_id: event.target.value })} placeholder="my-provider" />
            </label>
            <label>
              显示名称
              <input value={draft.display_name} onChange={(event) => updateDraft({ display_name: event.target.value })} placeholder="我的模型服务" />
            </label>
            <label>
              Base URL
              <input value={draft.base_url ?? ""} onChange={(event) => updateDraft({ base_url: event.target.value })} placeholder="https://api.example.com/v1" />
            </label>
            <label>
              Base URL 环境变量
              <input value={draft.base_url_env ?? ""} onChange={(event) => updateDraft({ base_url_env: event.target.value })} placeholder="LOCAL_LLM_BASE_URL" />
            </label>
            <label>
              超时秒数
              <input type="number" min={1} max={600} value={draft.default_timeout_seconds ?? 30} onChange={(event) => updateDraft({ default_timeout_seconds: Number(event.target.value) || 30 })} />
            </label>
          </div>
          {draft.provider_type === "relay" ? (
            <p className="muted">中转站 / Relay 只表示兼容 API 的 base URL 配置；本项目不是 API 转售服务，也不提供在线代理。</p>
          ) : null}
        </SectionCard>

        <SectionCard title="2. API Key 来源" description="选择密钥来源。临时 Key 只用于本次手动测试，不会进入保存的 ProviderProfile。">
          <div className="secret-mode-grid" data-testid="v37-provider-secret-mode">
            {([
              ["transient", "临时输入，仅用于本次测试"],
              ["api_key_env", "使用环境变量，例如 OPENAI_API_KEY"],
              ["secret_ref", "使用 secret_ref"],
              ["local_secret_ref", "使用本地 local_secret_ref"],
              ["none", "无需 API Key"]
            ] as Array<[ProviderSecretInputMode, string]>).map(([mode, label]) => (
              <label key={mode}>
                <input type="radio" name="provider-secret-mode" checked={secretMode === mode} onChange={() => updateSecretMode(mode)} />
                {label}
              </label>
            ))}
          </div>
          {secretMode === "transient" ? (
            <label>
              临时 API Key
              <input ref={transientKeyRef} type="password" autoComplete="off" placeholder="仅本次请求使用，不保存" aria-label="临时 API Key，仅本次测试使用" />
            </label>
          ) : null}
          {secretMode === "api_key_env" ? (
            <label>
              环境变量名
              <input value={draft.api_key_env ?? ""} onChange={(event) => updateDraft({ api_key_env: event.target.value })} placeholder="OPENAI_API_KEY" />
            </label>
          ) : null}
          {secretMode === "secret_ref" ? (
            <label>
              secret_ref
              <input value={draft.secret_ref ?? ""} onChange={(event) => updateDraft({ secret_ref: event.target.value })} placeholder="providers/main" />
            </label>
          ) : null}
          {secretMode === "local_secret_ref" ? (
            <label>
              local_secret_ref
              <input value={draft.local_secret_ref ?? ""} onChange={(event) => updateDraft({ local_secret_ref: event.target.value })} placeholder="providers/main" />
            </label>
          ) : null}
          <p className="muted">已保存密钥不会在 UI 中显示；Authorization header 与 provider raw response 也不会渲染。</p>
        </SectionCard>
      </div>

      <div className="studio-grid two-column-grid">
        <SectionCard title="3. 手动测试连接" description="真实连接只会在你点击按钮并勾选允许真实连接时发生；测试脚本仍使用 fake provider。">
          <label>
            <input type="checkbox" checked={allowRealProviderCall} onChange={(event) => setAllowRealProviderCall(event.target.checked)} />
            本次点击允许连接真实 Provider
          </label>
          <p className="muted" data-testid="v37-provider-manual-test-safe-hint">手动 Test Connection：只有用户点击测试连接时才会连接真实 Provider；连接失败只显示中文安全提示和 safe error type，不显示 API key、Authorization header 或 raw provider error。</p>
          <div className="button-row">
            <button type="button" data-testid="v37-provider-wizard-manual-test" onClick={() => void runWizardAction(handleTestConnection)}>手动 Test Connection / 测试连接</button>
            <button type="button" onClick={() => void runWizardAction(async () => { await onSaveProfile(draft); })}>保存安全配置</button>
          </div>
          <p className="muted">
            当前状态：{providerStatusToChinese(lastStatus)}
            {hasPersistedSecret ? "；已配置安全密钥引用。" : "；尚未配置持久密钥引用。"}
          </p>
        </SectionCard>

        <SectionCard title="4. 读取模型列表 / 手动添加" description="支持 /v1/models、custom model_list_endpoint 和手动 model_id。">
          <label>
            自定义模型列表端点
            <input value={modelListEndpoint} onChange={(event) => setModelListEndpoint(event.target.value)} placeholder="/v1/models 或 /custom/models" />
          </label>
          <div className="button-row">
            <button type="button" onClick={() => void runWizardAction(() => handleFetchModels(false))}>读取模型列表</button>
            <button type="button" onClick={() => void runWizardAction(() => handleFetchModels(true))}>同步为 ModelProfile</button>
          </div>
          <label>
            手动添加 model_id
            <input value={manualModelId} onChange={(event) => setManualModelId(event.target.value)} placeholder="gpt-4.1-mini 或 local-model" />
          </label>
          <button type="button" onClick={addManualModel}>添加 model_id</button>
          {fetchReport ? <p className="muted">模型读取状态：{providerReportStatusToChinese(fetchReport.status, fetchReport.safe_message)}</p> : null}
        </SectionCard>
      </div>

      <SectionCard title="5. 默认模型与按模式分配" description="默认模型是 ProviderProfile 中的第一个 ModelProfile；完整分配在 Model Assignment 面板完成。">
        <div className="form-grid">
          <label>
            默认模型
            <select value={defaultModelId} onChange={(event) => selectDefaultModel(event.target.value)}>
              <option value="">请选择模型</option>
              {availableModels.map((modelId) => <option key={modelId} value={modelId}>{modelId}</option>)}
            </select>
          </label>
          <button type="button" onClick={onOpenAssignment}>打开按模式分配模型</button>
        </div>
        <ItemList
          emptyText="还没有模型。请读取模型列表，或手动添加 model_id。"
          items={draft.model_profiles.map((model) => (
            <span key={model.model_id}>
              {model.model_id} {model.supports_json ? "JSON" : "文本"} {model.supports_streaming ? "streaming" : ""}
            </span>
          ))}
        />
      </SectionCard>

      <div className="button-row">
        <button type="button" onClick={() => setCurrentStep(Math.max(0, currentStep - 1))} disabled={currentStep === 0}>上一步</button>
        <button type="button" onClick={() => setCurrentStep(Math.min(PROVIDER_SETUP_WIZARD_STEPS.length - 1, currentStep + 1))} disabled={currentStep >= PROVIDER_SETUP_WIZARD_STEPS.length - 1}>下一步</button>
        <button type="button" onClick={() => void runWizardAction(async () => { await onSaveProfile(draft); })}>保存配置并回到首页使用</button>
      </div>
      {message ? (
        <div className="provider-wizard-message" role="status">
          <strong>安全提示</strong>
          <p>{toErrorMessage(message)}</p>
          <p className="muted">下一步：检查 Base URL、密钥来源、模型列表端点，或手动添加 model_id。错误信息已脱敏。</p>
        </div>
      ) : null}
    </section>
  );
}

function ProviderConnectivityDashboard({
  profiles,
  matrix,
  statusById,
  lastTestedById,
  usageSummary,
  recentUsage,
  usageByProvider,
  modelAssignmentOpen,
  isLoading,
  cacheStatuses,
  projectId,
  onChecklistRefresh,
  onTestConnection,
  onFetchModels,
  onRefreshModels,
  onOpenModelAssignment,
  onOpenProviderSetup
}: {
  profiles: ProviderProfileSummary[];
  matrix: ProviderModelCapabilityMatrix | null;
  statusById: Record<string, Record<string, unknown>>;
  lastTestedById: Record<string, string>;
  usageSummary: ModelUsageSummary | null;
  recentUsage: ModelUsageRecord[];
  usageByProvider: CostLatencyGroupSummary[];
  modelAssignmentOpen: boolean;
  isLoading: boolean;
  cacheStatuses: SafeApiCacheStatus[];
  projectId: string;
  onChecklistRefresh: () => void;
  onTestConnection: (profileId: string) => void;
  onFetchModels: () => void;
  onRefreshModels: () => void;
  onOpenModelAssignment: () => void;
  onOpenProviderSetup: () => void;
}) {
  const providerRows = useMemo(
    () => profiles.map((profile) => buildProviderConnectivityRow(profile, statusById[profile.provider_profile_id], lastTestedById[profile.provider_profile_id])),
    [lastTestedById, profiles, statusById]
  );
  const modelRows = useMemo(() => buildProviderModelListRows(profiles, matrix), [matrix, profiles]);
  const slowWarnings = useMemo(
    () => buildSlowProviderWarnings(providerRows, usageSummary, usageByProvider, recentUsage),
    [providerRows, recentUsage, usageByProvider, usageSummary]
  );
  const [modelSearch, setModelSearch] = useState("");
  const debouncedModelSearch = useDebouncedValue(modelSearch, 180);
  const [capabilityFilter, setCapabilityFilter] = useState<ProviderModelCapabilityFilter>("all");
  const [enabledFilter, setEnabledFilter] = useState<ProviderModelEnabledFilter>("all");
  const [useCaseFilter, setUseCaseFilter] = useState("all");
  const [modelPage, setModelPage] = useState(0);
  const [manualProviderId, setManualProviderId] = useState(profiles[0]?.provider_profile_id ?? "");
  const [manualModelId, setManualModelId] = useState("");
  const [manualSupportsJson, setManualSupportsJson] = useState(false);
  const [manualSupportsStreaming, setManualSupportsStreaming] = useState(false);
  const [manualSupportsTools, setManualSupportsTools] = useState(false);
  const [manualModelMessage, setManualModelMessage] = useState("");

  const recommendedUseCases = useMemo(
    () => Array.from(new Set(modelRows.flatMap((row) => row.recommendedUseCases))).sort(),
    [modelRows]
  );
  const filteredModelRows = useMemo(
    () =>
      modelRows.filter((row) => {
        if (capabilityFilter !== "all" && !modelRowSupports(row, capabilityFilter)) return false;
        if (enabledFilter === "enabled" && !row.enabled) return false;
        if (enabledFilter === "disabled" && row.enabled) return false;
        if (useCaseFilter !== "all" && !row.recommendedUseCases.includes(useCaseFilter)) return false;
        return safeSearchMatches(buildSafeSearchIndex([row.providerName, row.providerId, row.providerType, row.modelId, row.displayName, row.recommendedUseCases.join(" "), row.warnings.join(" ")]), debouncedModelSearch);
      }),
    [capabilityFilter, debouncedModelSearch, enabledFilter, modelRows, useCaseFilter]
  );
  const modelPageCount = Math.max(1, Math.ceil(filteredModelRows.length / PROVIDER_MODEL_PAGE_SIZE));
  const clampedModelPage = Math.min(modelPage, modelPageCount - 1);
  const modelWindowStart = clampedModelPage * PROVIDER_MODEL_PAGE_SIZE;
  const visibleModels = filteredModelRows.slice(modelWindowStart, modelWindowStart + PROVIDER_MODEL_PAGE_SIZE);

  useEffect(() => {
    setModelPage(0);
  }, [capabilityFilter, debouncedModelSearch, enabledFilter, useCaseFilter]);

  useEffect(() => {
    if (!manualProviderId && profiles[0]?.provider_profile_id) {
      setManualProviderId(profiles[0].provider_profile_id);
    }
  }, [manualProviderId, profiles]);

  async function addManualModelProfile() {
    setManualModelMessage("");
    const modelId = manualModelId.trim();
    const profile = profiles.find((item) => item.provider_profile_id === manualProviderId);
    if (!profile) {
      setManualModelMessage("请选择 Provider 后再添加模型。");
      return;
    }
    if (!modelId) {
      setManualModelMessage("请输入 model_id。");
      return;
    }
    if (profile.model_profiles.some((model) => model.model_id === modelId)) {
      setManualModelMessage("这个 model_id 已存在。");
      return;
    }
    const nextModels: ProviderModelPatchItem[] = [
      ...profile.model_profiles,
      {
        model_id: modelId,
        display_name: modelId,
        provider_profile_id: profile.provider_profile_id,
        supports_text: true,
        supports_json: manualSupportsJson,
        supports_streaming: manualSupportsStreaming,
        supports_tools: manualSupportsTools,
        recommended_use_cases: [],
        enabled: true
      }
    ];
    try {
      await patchProjectProviderModels(projectId, profile.provider_profile_id, nextModels);
      setManualModelMessage("已保存手动 ModelProfile。");
      setManualModelId("");
      onRefreshModels();
    } catch (error) {
      setManualModelMessage(toErrorMessage(error));
    }
  }

  return (
    <section className="studio-section provider-connectivity-dashboard" data-large-provider-model-list="windowed" data-testid="v37-provider-model-list-final">
      <div className="authoring-pane-header">
        <div>
          <h4>模型列表与 Provider 状态</h4>
          <p className="muted">只显示安全模型 metadata、连接状态和路由健康摘要。API Key、Authorization header 与 raw provider response 不会显示。</p>
        </div>
        <div className="button-row">
          <button type="button" onClick={onFetchModels} disabled={isLoading}>
            {isLoading ? "读取中..." : "读取模型"}
          </button>
          <button type="button" onClick={onRefreshModels}>刷新模型</button>
          <button type="button" onClick={onOpenModelAssignment}>模型分配</button>
          <button type="button" onClick={onOpenProviderSetup}>Provider 设置</button>
        </div>
      </div>
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Provider" value={String(profiles.length)}>
          <p>{profiles.length ? "已从本地项目 metadata 读取 ProviderProfile。" : "还没有 Provider。请先配置模型服务。"}</p>
        </DashboardCard>
        <DashboardCard title="模型" value={String(modelRows.length)}>
          <p>筛选后 {filteredModelRows.length} 个；当前窗口只渲染 {visibleModels.length} 行。</p>
        </DashboardCard>
        <DashboardCard title="提示" value={String(slowWarnings.length)}>
          <p>慢 Provider 提示只显示安全摘要，不包含 prompt/output。</p>
        </DashboardCard>
      </div>
      <div className="studio-grid two-column-grid">
        <SectionCard title="Provider 列表" description="连接状态缓存只保存安全 metadata，不保存 secret。">
          <ItemList
            emptyText="Provider 列表为空。"
            items={providerRows.map((row) => (
              <span key={row.providerId}>
                <ProviderConnectionStatusBadge status={row.connectionStatus} /> {row.displayName} ({row.providerType}) - {row.modelCount} 个模型 - {row.lastTestedTime}
                {row.stale ? " - stale" : ""} - {row.warnings.join("; ") || "no warnings"}
                <button type="button" data-testid="v37-manual-provider-test-connection" onClick={() => onTestConnection(row.providerId)}>手动 Test Connection</button>
              </span>
            ))}
          />
        </SectionCard>
        <SectionCard title="安全缓存" description="可手动刷新；stale 状态不会自动调用 Provider。">
          {cacheStatuses.length ? (
            cacheStatuses.map((status) => <SafeApiCacheStatusPanel key={status.key} status={status} onRefresh={onRefreshModels} />)
          ) : (
            <SafeApiCacheStatusPanel status={null} onRefresh={onRefreshModels} />
          )}
        </SectionCard>
      </div>
      {slowWarnings.length ? (
        <SectionCard title="慢 Provider 提示" description="不显示 raw provider error、prompt、output、API key 或 Authorization header。">
          <ItemList
            emptyText="No slow provider warnings."
            items={slowWarnings.map((warning) => (
              <span key={warning.id}>
                <QualitySeverityBadge severity={warning.severity} /> {warning.source}: {warning.safeSummary} Suggested: {warning.suggestedActions.join(", ")}
              </span>
            ))}
          />
        </SectionCard>
      ) : null}
      <SectionCard title="手动添加模型" description="用于 Provider 不支持模型列表或需要补充 model_id 的场景；保存为安全 ModelProfile metadata。">
        <span className="sr-only">manual model add saves ModelProfile metadata and never stores API keys.</span>
        <div className="form-grid">
          <label>
            Provider
            <select value={manualProviderId} onChange={(event) => setManualProviderId(event.target.value)}>
              <option value="">请选择 Provider</option>
              {profiles.map((profile) => <option key={profile.provider_profile_id} value={profile.provider_profile_id}>{profile.display_name} / {profile.provider_profile_id}</option>)}
            </select>
          </label>
          <label>
            model_id
            <input value={manualModelId} onChange={(event) => setManualModelId(event.target.value)} placeholder="gpt-4.1-mini / local-model" />
          </label>
          <label>
            <input type="checkbox" checked={manualSupportsJson} onChange={(event) => setManualSupportsJson(event.target.checked)} />
            JSON / 结构化输出
          </label>
          <label>
            <input type="checkbox" checked={manualSupportsStreaming} onChange={(event) => setManualSupportsStreaming(event.target.checked)} />
            流式
          </label>
          <label>
            <input type="checkbox" checked={manualSupportsTools} onChange={(event) => setManualSupportsTools(event.target.checked)} />
            工具调用
          </label>
        </div>
        <button type="button" onClick={() => void addManualModelProfile()}>保存手动 ModelProfile</button>
        {manualModelMessage ? <p className="muted">{manualModelMessage}</p> : null}
      </SectionCard>
      <FilterToolbar>
        <label>
          搜索模型
          <input value={modelSearch} onChange={(event) => setModelSearch(event.target.value)} placeholder="provider / model / 使用场景" />
        </label>
        <label>
          能力
          <select value={capabilityFilter} onChange={(event) => setCapabilityFilter(event.target.value as ProviderModelCapabilityFilter)}>
            <option value="all">全部能力</option>
            <option value="supports_text">文本</option>
            <option value="supports_json">JSON / 结构化输出</option>
            <option value="supports_streaming">流式</option>
            <option value="supports_tools">工具调用</option>
          </select>
        </label>
        <label>
          启用状态
          <select value={enabledFilter} onChange={(event) => setEnabledFilter(event.target.value as ProviderModelEnabledFilter)}>
            <option value="all">全部</option>
            <option value="enabled">仅启用</option>
            <option value="disabled">仅禁用</option>
          </select>
        </label>
        <label>
          使用场景
          <select value={useCaseFilter} onChange={(event) => setUseCaseFilter(event.target.value)}>
            <option value="all">全部场景</option>
            {recommendedUseCases.map((useCase) => (
              <option key={useCase} value={useCase}>{useCase}</option>
            ))}
          </select>
        </label>
      </FilterToolbar>
      <div className="section-heading-row">
        <p className="muted">
          当前显示 {filteredModelRows.length ? modelWindowStart + 1 : 0}-{Math.min(modelWindowStart + visibleModels.length, filteredModelRows.length)} / {filteredModelRows.length} 个筛选模型。
        </p>
        <div className="pagination-controls" aria-label="Provider model list pagination">
          <button type="button" onClick={() => setModelPage(0)} disabled={clampedModelPage === 0}>首页</button>
          <button type="button" onClick={() => setModelPage(Math.max(clampedModelPage - 1, 0))} disabled={clampedModelPage === 0}>上一页</button>
          <span>第 {clampedModelPage + 1} / {modelPageCount} 页</span>
          <button type="button" onClick={() => setModelPage(Math.min(clampedModelPage + 1, modelPageCount - 1))} disabled={clampedModelPage >= modelPageCount - 1}>下一页</button>
          <button type="button" onClick={() => setModelPage(modelPageCount - 1)} disabled={clampedModelPage >= modelPageCount - 1}>末页</button>
        </div>
      </div>
      <div className="provider-model-window" data-rendered-count={visibleModels.length}>
        {visibleModels.length ? visibleModels.map((row) => (
          <article className="provider-model-row" key={row.id}>
            <div>
              <strong>{row.displayName || row.modelId}</strong>
              <p className="muted">{row.providerName} / {row.providerType}</p>
            </div>
            <div className="provider-model-capability-badges">
              <ModelCapabilityBadge label="文本" supported={row.supportsText} />
              <ModelCapabilityBadge label="JSON" supported={row.supportsJson} />
              <ModelCapabilityBadge label="流式" supported={row.supportsStreaming} />
              <ModelCapabilityBadge label="工具调用" supported={row.supportsTools} />
            </div>
            <p className="muted">{row.recommendedUseCases.join(", ") || "暂无推荐场景。"}</p>
            <p className="muted">{row.warnings.join("; ") || "暂无 warning。"}</p>
          </article>
        )) : (
          <EmptyState title="没有匹配的模型。" detail="可以清空搜索/能力筛选，或手动添加 model_id。raw provider response 不会显示。" />
        )}
      </div>
      {modelAssignmentOpen ? <ProviderModelAssignmentPanel projectId={projectId} profiles={profiles} onChecklistRefresh={onChecklistRefresh} /> : null}
    </section>
  );
}

function ProviderModelAssignmentPanel({ projectId, profiles, onChecklistRefresh }: { projectId: string; profiles: ProviderProfileSummary[]; onChecklistRefresh: () => void }) {
  const [summary, setSummary] = useState<ProjectProviderModelAssignmentSummary | null>(null);
  const [message, setMessage] = useState("");
  const fallbackProfile = profiles.find((profile) => profile.provider_type === "mock" || profile.provider_type === "local_stub") ?? profiles[0];
  const defaultProviderId = profiles[0]?.provider_profile_id ?? "local_stub";
  const defaultModelId = profiles[0]?.model_profiles[0]?.model_id ?? "local_stub";
  const [assignmentDrafts, setAssignmentDrafts] = useState<Record<string, ProviderRoutingRule>>(() =>
    Object.fromEntries(PROVIDER_MODEL_ASSIGNMENT_USE_CASES.map((item) => [
      item.value,
      buildDefaultRoutingRule(item.value, defaultProviderId, defaultModelId, fallbackProfile?.provider_profile_id ?? "mock", fallbackProfile?.model_profiles[0]?.model_id ?? "mock")
    ]))
  );

  useEffect(() => {
    setAssignmentDrafts((current) => {
      const next = { ...current };
      for (const item of PROVIDER_MODEL_ASSIGNMENT_USE_CASES) {
        if (!next[item.value]) {
          next[item.value] = buildDefaultRoutingRule(item.value, defaultProviderId, defaultModelId, fallbackProfile?.provider_profile_id ?? "mock", fallbackProfile?.model_profiles[0]?.model_id ?? "mock");
        }
      }
      return next;
    });
  }, [defaultModelId, defaultProviderId, fallbackProfile?.model_profiles, fallbackProfile?.provider_profile_id]);

  const providerOptions = useMemo(
    () => Array.from(new Set([...profiles.map((profile) => profile.provider_profile_id), "mock", "local_stub"])).filter(Boolean),
    [profiles]
  );
  const currentConfig = useMemo<ProviderRoutingConfig>(
    () => ({ rules: PROVIDER_MODEL_ASSIGNMENT_USE_CASES.map((item) => assignmentDrafts[item.value]).filter(Boolean) }),
    [assignmentDrafts]
  );

  function updateRule(useCase: ProviderRoutingUseCase, patch: Partial<ProviderRoutingRule>) {
    setAssignmentDrafts((current) => {
      const existing = current[useCase] ?? buildDefaultRoutingRule(useCase, defaultProviderId, defaultModelId, fallbackProfile?.provider_profile_id ?? "mock", fallbackProfile?.model_profiles[0]?.model_id ?? "mock");
      return {
        ...current,
        [useCase]: {
          ...existing,
          ...patch,
          require_json_support: patch.require_json_support ?? existing.require_json_support ?? routingUseCaseRequiresJson(useCase)
        }
      };
    });
  }

  function applySummaryRules(nextSummary: ProjectProviderModelAssignmentSummary) {
    setSummary(nextSummary);
    setAssignmentDrafts((current) => {
      const next = { ...current };
      for (const rule of nextSummary.rules) {
        next[rule.use_case] = rule;
      }
      return next;
    });
  }

  async function run(action: () => Promise<void>) {
    setMessage("");
    try {
      await action();
    } catch (error) {
      setMessage(toErrorMessage(error));
    }
  }

  return (
    <section className="studio-section model-assignment-panel" data-testid="v37-model-assignment-final">
      <div className="authoring-pane-header">
        <div>
          <h4>Provider Model Assignment by Mode / 按场景分配模型</h4>
          <p className="muted">按小说、Tavern、World、Cross-Mode、质量检查分配模型。Provider Gateway 仍是唯一运行时模型入口，模型不会决定世界事实。</p>
        </div>
        <div className="button-row">
          <button type="button" onClick={() => void run(async () => applySummaryRules(await fetchProjectProviderModelAssignments(projectId)))}>
            读取分配
          </button>
          <button type="button" onClick={() => void run(async () => applySummaryRules(await validateProjectProviderModelAssignments(projectId, currentConfig)))}>
            校验 routing
          </button>
          <button type="button" onClick={() => void run(async () => {
            applySummaryRules(await saveProjectProviderModelAssignments(projectId, currentConfig));
            setMessage("模型分配已保存。未保存 API key、transient key 或 provider secret。");
            onChecklistRefresh();
          })}>
            保存全部分配
          </button>
        </div>
      </div>
      <ErrorPanel message={message} compact />
      <div className="model-assignment-grid">
        {PROVIDER_MODEL_ASSIGNMENT_USE_CASES.map((item) => {
          const rule = assignmentDrafts[item.value] ?? buildDefaultRoutingRule(item.value, defaultProviderId, defaultModelId, fallbackProfile?.provider_profile_id ?? "mock", fallbackProfile?.model_profiles[0]?.model_id ?? "mock");
          const primaryModels = modelOptionsForProvider(profiles, rule.primary_provider_id, rule.primary_model_id);
          const fallbackModels = modelOptionsForProvider(profiles, rule.fallback_provider_id ?? "", rule.fallback_model_id ?? "");
          const selectedModel = findProviderModel(profiles, rule.primary_provider_id, rule.primary_model_id);
          const jsonWarning = routingUseCaseRequiresJson(item.value) && !selectedModel?.supports_json;
          const validationWarnings = summary?.validation_reports.find((report) => report.rule.use_case === item.value)?.warnings ?? [];
          return (
            <article className={`model-assignment-card ${jsonWarning ? "warning" : ""}`} key={item.value}>
              <div className="model-assignment-heading">
                <h5>{item.label}</h5>
                {jsonWarning ? <span className="status-pill warning">需要 JSON / 结构化输出</span> : <span className="status-pill pass">可配置</span>}
              </div>
              <div className="form-grid">
                <label>
                  主 Provider
                  <select value={rule.primary_provider_id} onChange={(event) => {
                    const providerId = event.target.value;
                    updateRule(item.value, {
                      primary_provider_id: providerId,
                      primary_model_id: modelOptionsForProvider(profiles, providerId, "")[0] ?? ""
                    });
                  }}>
                    {providerOptions.map((providerId) => <option key={providerId} value={providerId}>{providerId}</option>)}
                  </select>
                </label>
                <label>
                  主模型
                  <select value={rule.primary_model_id} onChange={(event) => updateRule(item.value, { primary_model_id: event.target.value })}>
                    {primaryModels.map((modelId) => <option key={modelId} value={modelId}>{modelId}</option>)}
                  </select>
                </label>
                <label>
                  fallback Provider
                  <select value={rule.fallback_provider_id ?? ""} onChange={(event) => {
                    const providerId = event.target.value;
                    updateRule(item.value, {
                      fallback_provider_id: providerId || null,
                      fallback_model_id: providerId ? modelOptionsForProvider(profiles, providerId, "")[0] ?? "" : null
                    });
                  }}>
                    <option value="">不使用 fallback</option>
                    {providerOptions.map((providerId) => <option key={providerId} value={providerId}>{providerId}</option>)}
                  </select>
                </label>
                <label>
                  fallback 模型
                  <select value={rule.fallback_model_id ?? ""} onChange={(event) => updateRule(item.value, { fallback_model_id: event.target.value || null })}>
                    <option value="">不使用 fallback</option>
                    {fallbackModels.map((modelId) => <option key={modelId} value={modelId}>{modelId}</option>)}
                  </select>
                </label>
                <label>
                  <input type="checkbox" checked={Boolean(rule.require_json_support) || routingUseCaseRequiresJson(item.value)} onChange={(event) => updateRule(item.value, { require_json_support: event.target.checked || routingUseCaseRequiresJson(item.value) })} />
                  需要 JSON / 结构化输出
                </label>
              </div>
              {item.value === "world_intent_parse" ? <p className="muted">世界输入解析必须使用支持 JSON / 结构化输出的模型，否则无法稳定解析玩家意图。</p> : null}
              {validationWarnings.length ? <p className="muted">{validationWarnings.join("; ")}</p> : null}
            </article>
          );
        })}
      </div>
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="JSON 提示" value="world_intent_parse required">
          <p>世界输入解析、质量检查、记忆摘要与 Cross-Mode 草稿建议使用 JSON / 结构化输出模型。</p>
        </DashboardCard>
        <DashboardCard title="Fallback" value="supported">
          <p>fallback chain 只是 routing metadata，不会自动调用 Provider。</p>
        </DashboardCard>
        <DashboardCard title="校验" value={summary?.validation_reports.every((report) => report.ok) ? "ok" : summary ? "warnings" : "not loaded"}>
          <p>{summary?.warnings.join(", ") || "读取或校验分配后会显示安全 warning。"}</p>
        </DashboardCard>
      </div>
      {summary ? (
        <ItemList
          emptyText="暂无模型分配。"
          items={summary.rules.map((rule) => (
            <span key={`${rule.use_case}-${rule.primary_provider_id}-${rule.primary_model_id}`}>
              {providerUseCaseLabel(rule.use_case)}: {rule.primary_provider_id}/{rule.primary_model_id}
              {rule.fallback_provider_id ? ` -> ${rule.fallback_provider_id}/${rule.fallback_model_id}` : ""}
              {summary.validation_reports.find((report) => report.rule.use_case === rule.use_case)?.warnings.length
                ? ` (${summary.validation_reports.find((report) => report.rule.use_case === rule.use_case)?.warnings.join(", ")})`
                : ""}
            </span>
          ))}
        />
      ) : (
        <EmptyState title="还没有读取模型分配。" detail="读取、校验或保存本地模型分配。secret 不属于 routing metadata。" />
      )}
    </section>
  );
}

function ProviderCapabilityMatrixPanel({ matrix, profiles }: { matrix: ProviderModelCapabilityMatrix | null; profiles: ProviderProfileSummary[] }) {
  const matrixSafeSummary = useMemo(() => buildProviderCapabilityMatrixSafeSummary(matrix, profiles), [matrix, profiles]);
  const [providerFilter, setProviderFilter] = useState("all");
  const [capabilityFilter, setCapabilityFilter] = useState<ProviderCapabilityMatrixFilter>("all");
  const [useCaseFilter, setUseCaseFilter] = useState("all");
  const [matrixPageSize, setMatrixPageSize] = useState(25);
  const [matrixPageIndex, setMatrixPageIndex] = useState(0);

  const filteredMatrixRows = useMemo(
    () =>
      matrixSafeSummary.rows.filter((row) => {
        if (providerFilter !== "all" && row.providerId !== providerFilter) return false;
        if (capabilityFilter !== "all" && !capabilityMatrixRowSupports(row, capabilityFilter)) return false;
        if (useCaseFilter !== "all" && !row.recommendedUseCases.includes(useCaseFilter)) return false;
        return true;
      }),
    [capabilityFilter, matrixSafeSummary.rows, providerFilter, useCaseFilter]
  );
  const matrixPageCount = Math.max(1, Math.ceil(filteredMatrixRows.length / matrixPageSize));
  const clampedMatrixPageIndex = Math.min(matrixPageIndex, matrixPageCount - 1);
  const matrixWindowStart = clampedMatrixPageIndex * matrixPageSize;
  const matrixWindowEnd = Math.min(matrixWindowStart + matrixPageSize, filteredMatrixRows.length);
  const visibleMatrixRows = filteredMatrixRows.slice(matrixWindowStart, matrixWindowEnd);

  useEffect(() => {
    setMatrixPageIndex(0);
  }, [capabilityFilter, matrixPageSize, providerFilter, useCaseFilter]);

  return (
    <section className="section-card capability-matrix-panel" data-windowed-capability-matrix="true">
      <div className="authoring-pane-header">
        <div>
          <h4>Capability Matrix</h4>
          <p className="muted">Cached safe summary of provider/model capability metadata. Raw provider metadata and API keys are not rendered.</p>
        </div>
        <span className="badge">{matrixSafeSummary.rowCount} matrix rows</span>
      </div>
      <div className="timeline-summary">
        <span>{matrixSafeSummary.providerCount} providers</span>
        <span>{matrixSafeSummary.warningCount} warnings</span>
        <span>{matrixSafeSummary.blockerCount} blockers</span>
        <span>Generated {matrixSafeSummary.generatedAt || "not loaded"}</span>
      </div>
      <FilterToolbar>
        <label>
          Provider
          <select value={providerFilter} onChange={(event) => setProviderFilter(event.target.value)}>
            <option value="all">All providers</option>
            {matrixSafeSummary.providers.map((provider) => (
              <option key={provider.providerId} value={provider.providerId}>{provider.providerName} ({provider.rowCount})</option>
            ))}
          </select>
        </label>
        <label>
          Capability
          <select value={capabilityFilter} onChange={(event) => setCapabilityFilter(event.target.value as ProviderCapabilityMatrixFilter)}>
            <option value="all">All capabilities</option>
            <option value="supports_text">supports_text</option>
            <option value="supports_json">supports_json</option>
            <option value="supports_streaming">supports_streaming</option>
            <option value="supports_tools">supports_tools</option>
          </select>
        </label>
        <label>
          Use case
          <select value={useCaseFilter} onChange={(event) => setUseCaseFilter(event.target.value)}>
            <option value="all">All use cases</option>
            {matrixSafeSummary.useCases.map((useCase) => <option key={useCase} value={useCase}>{useCase}</option>)}
          </select>
        </label>
        <label>
          Rows
          <select value={matrixPageSize} onChange={(event) => setMatrixPageSize(Number(event.target.value))}>
            {[10, 25, 50, 100].map((size) => <option key={size} value={size}>{size}</option>)}
          </select>
        </label>
      </FilterToolbar>
      {!matrix ? (
        <EmptyState title="No capability matrix loaded." detail="Load provider profiles to build a local safe capability matrix summary." />
      ) : filteredMatrixRows.length === 0 ? (
        <EmptyState title="No matrix rows match these filters." detail="Try a different provider, capability, or use case. Warnings are preserved when rows match." />
      ) : (
        <>
          <div className="section-heading-row">
            <p className="muted">
              Rendering {matrixWindowStart + 1}-{matrixWindowEnd} of {filteredMatrixRows.length} filtered matrix row(s).
            </p>
            <div className="pagination-controls" aria-label="Capability matrix pagination">
              <button type="button" onClick={() => setMatrixPageIndex(0)} disabled={clampedMatrixPageIndex === 0}>First</button>
              <button type="button" onClick={() => setMatrixPageIndex(Math.max(clampedMatrixPageIndex - 1, 0))} disabled={clampedMatrixPageIndex === 0}>Previous</button>
              <span>Page {clampedMatrixPageIndex + 1} / {matrixPageCount}</span>
              <button type="button" onClick={() => setMatrixPageIndex(Math.min(clampedMatrixPageIndex + 1, matrixPageCount - 1))} disabled={clampedMatrixPageIndex >= matrixPageCount - 1}>Next</button>
              <button type="button" onClick={() => setMatrixPageIndex(matrixPageCount - 1)} disabled={clampedMatrixPageIndex >= matrixPageCount - 1}>Last</button>
            </div>
          </div>
          <div className="capability-matrix-window" data-rendered-count={visibleMatrixRows.length}>
            {visibleMatrixRows.map((row) => (
              <article className="capability-matrix-row" key={row.id}>
                <div>
                  <strong>{row.modelId}</strong>
                  <p className="muted">{row.providerName} / {row.providerId}</p>
                </div>
                <div className="provider-model-capability-badges">
                  <ModelCapabilityBadge label="text" supported={row.supportsText} />
                  <ModelCapabilityBadge label="json" supported={row.supportsJson} />
                  <ModelCapabilityBadge label="streaming" supported={row.supportsStreaming} />
                  <ModelCapabilityBadge label="tools" supported={row.supportsTools} />
                </div>
                <p className="muted">{row.recommendedUseCases.join(", ") || "No recommended use cases."}</p>
                <p className="muted">{[...row.warnings, ...row.disabledReasons].join("; ") || "No warnings."}</p>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function ProviderUsageCostDashboard({
  projectId,
  summary,
  recent,
  usageByMode,
  usageByProvider,
  usageRange,
  onRangeChange,
  onLoad
}: {
  projectId: string;
  summary: ModelUsageSummary | null;
  recent: ModelUsageRecord[];
  usageByMode: CostLatencyGroupSummary[];
  usageByProvider: CostLatencyGroupSummary[];
  usageRange: number | undefined;
  onRangeChange: (range: number | undefined) => void;
  onLoad: () => void;
}) {
  const successErrorRows = summary
    ? [
        { key: "success", count: summary.successes, failures: 0, total_tokens_estimated: summary.total_input_tokens_estimated + summary.total_output_tokens_estimated, total_cost_estimated: summary.total_cost_estimated, latency_p50_ms: summary.latency_p50_ms, latency_p95_ms: summary.latency_p95_ms },
        { key: "error", count: summary.failures, failures: summary.failures, total_tokens_estimated: 0, total_cost_estimated: 0, latency_p50_ms: 0, latency_p95_ms: 0 }
      ]
    : [];
  const totalTokens = summary ? summary.total_input_tokens_estimated + summary.total_output_tokens_estimated : 0;

  return (
    <>
      <div className="authoring-pane-header">
        <div>
          <h4>Provider Usage / Cost Dashboard Pro</h4>
          <p className="muted">
            Local estimates for project {projectId}. Prompts, outputs, API keys, hidden facts, mature/private text, and raw state deltas are never displayed.
          </p>
        </div>
        <div className="button-row">
          <select value={usageRange ?? 0} onChange={(event) => onRangeChange(Number(event.target.value) || undefined)} aria-label="Usage time range">
            <option value={0}>All time</option>
            <option value={60}>Last hour</option>
            <option value={1440}>Last day</option>
            <option value={10080}>Last 7 days</option>
          </select>
          <button type="button" onClick={onLoad}>Load Project Usage</button>
        </div>
      </div>
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Usage Overview" value={summary ? String(summary.total_calls) : "empty"}>
          <p>{summary ? `${summary.successes} ok / ${summary.failures} errors` : "Usage API may be disabled or no local calls have been recorded."}</p>
        </DashboardCard>
        <DashboardCard title="Estimated Tokens" value={summary ? String(totalTokens) : "empty"}>
          <p>{summary ? `input ${summary.total_input_tokens_estimated} / output ${summary.total_output_tokens_estimated}` : "Token estimates only; prompt and output text are not stored here."}</p>
        </DashboardCard>
        <DashboardCard title="Estimated Cost" value={summary ? formatEstimatedCost(summary.total_cost_estimated) : "empty"}>
          <p>Cost is approximate local metadata, not billing-grade and never uploaded.</p>
        </DashboardCard>
        <DashboardCard title="Average Latency" value={summary ? formatDuration(summary.average_latency_ms) : "empty"}>
          <p>{summary ? `p50 ${formatDuration(summary.latency_p50_ms)} / p95 ${formatDuration(summary.latency_p95_ms)}` : "No latency summary."}</p>
        </DashboardCard>
        <DashboardCard title="Error Count" value={summary ? String(summary.failures) : "empty"}>
          <p>{summary ? `${Math.round(summary.error_rate * 100)}% error rate` : "No usage summary."}</p>
        </DashboardCard>
      </div>
      <div className="studio-grid two-column-grid">
        <UsageGroupList title="By provider" emptyText="No usage by provider." rows={usageByProvider} />
        <UsageGroupList title="By model" emptyText="No usage by model." rows={summary?.by_model ?? []} />
        <UsageGroupList title="By mode" emptyText="No usage by mode." rows={usageByMode} />
        <UsageUseCaseList rows={summary?.by_use_case ?? []} />
        <UsageGroupList title="By success/error" emptyText="No success/error usage summary." rows={successErrorRows} />
      </div>
      <ItemList
        emptyText="No project usage records."
        items={recent.map((record) => (
          <span key={record.usage_id}>
            {(record.mode ?? "mode")}/{record.use_case}: {record.provider_id}/{record.model_id} {record.success ? "ok" : record.error_type ?? "failed"} ({record.input_tokens_estimated} in / {record.output_tokens_estimated} out, {formatDuration(record.duration_ms)})
          </span>
        ))}
      />
      <p className="muted">
        Usage records contain metadata only: provider, model, mode, use case, token estimates, estimated cost, latency, and error type. Full prompt/output text and secrets are excluded.
      </p>
    </>
  );
}

function PromptProfileSafeSettings({ summary, onSelectPromptProfile }: { summary: StudioConfigSummary | null; onSelectPromptProfile: (profileId: string) => void }) {
  const [selectedProfileId, setSelectedProfileId] = useState(summary?.selected_prompt_profile_id ?? "");
  const profiles = summary?.prompt_profiles ?? [];
  useEffect(() => {
    setSelectedProfileId(summary?.selected_prompt_profile_id ?? "");
  }, [summary?.selected_prompt_profile_id]);

  return (
    <section className="studio-section">
      <div className="authoring-pane-header">
        <div>
          <h4>Prompt Profile 安全设置</h4>
          <p className="muted">Prompt Profile 选择只是本地 metadata。这里不显示 raw prompt、API key、hidden facts 或 provider secret。</p>
        </div>
        <StatusBadge label={summary?.local_only ? "本地优先" : "安全摘要未载入"} enabled={summary?.local_only} />
      </div>
      {summary ? (
        <>
          <div className="form-grid">
            <label>
              当前 Prompt Profile
              <select value={selectedProfileId} onChange={(event) => setSelectedProfileId(event.target.value)}>
                <option value="">选择一个 profile</option>
                {profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>{profile.name}</option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={() => {
                if (selectedProfileId) onSelectPromptProfile(selectedProfileId);
              }}
              disabled={!selectedProfileId}
            >
              选择 Profile
            </button>
          </div>
          <div className="studio-columns">
            <section>
              <h4>隐私说明</h4>
              <ul className="compact-list">
                {summary.privacy_notes.map((note) => <li key={note}>{note}</li>)}
              </ul>
            </section>
            <section>
              <h4>边界</h4>
              <ul className="compact-list">
                <li>Provider Gateway 仍是唯一模型入口。</li>
                <li>API keys 只存在于环境变量或本地 secret 引用中。</li>
                <li>Provider Connectivity 是本地配置能力，不是在线平台。</li>
                <li>World facts 仍由 World Engine 管理。</li>
              </ul>
            </section>
          </div>
        </>
      ) : (
        <EmptyState title="配置摘要不可用。" detail="安全摘要接口失败时，Prompt 设置页保持空状态，不显示敏感内容。" />
      )}
    </section>
  );
}

export function SettingsPrivacyPanel({
  selectedProjectId,
  summary,
  localConfigSummary,
  localConfigIssues = [],
  localEnvTemplate,
  currentWorkspace,
  recentProjectCount = 0,
  keyboardShortcutsEnabled = true,
  reducedMotionEnabled = false,
  error,
  onSelectPromptProfile,
  onRefreshLocalConfig = () => undefined,
  onGenerateLocalEnvTemplate = () => undefined,
  onClearRecentProjects = () => undefined,
  onToggleKeyboardShortcuts = () => undefined,
  onToggleReducedMotion = () => undefined,
  onOpenShortcutHelp = () => undefined,
  promptLabOnly = false
}: {
  selectedProjectId?: string;
  summary: StudioConfigSummary | null;
  localConfigSummary?: LocalConfigSummary | null;
  localConfigIssues?: LocalConfigIssue[];
  localEnvTemplate?: LocalEnvTemplateResponse | null;
  currentWorkspace?: ProjectWorkspace | null;
  recentProjectCount?: number;
  keyboardShortcutsEnabled?: boolean;
  reducedMotionEnabled?: boolean;
  error: string;
  onSelectPromptProfile: (profileId: string) => void;
  onRefreshLocalConfig?: () => void;
  onGenerateLocalEnvTemplate?: () => void;
  onClearRecentProjects?: () => void;
  onToggleKeyboardShortcuts?: (enabled: boolean) => void;
  onToggleReducedMotion?: (enabled: boolean) => void;
  onOpenShortcutHelp?: () => void;
  promptLabOnly?: boolean;
}) {
  const providerConfigured = Boolean(
    summary?.api_key_configured ||
    localConfigSummary?.api_key_configured ||
    summary?.llm_provider === "mock" ||
    summary?.llm_provider === "local_stub" ||
    localConfigSummary?.provider_type === "mock" ||
    localConfigSummary?.provider_type === "local_stub"
  );
  const debugEnabled = Boolean(localConfigSummary?.debug_api_enabled);
  const productSettingsSections = [
    {
      title: "General",
      cnTitle: "常规设置",
      status: selectedProjectId || currentWorkspace ? "ready" : "not checked",
      safeSummary: currentWorkspace
        ? `当前工作区：${currentWorkspace.name}（${currentWorkspace.path_redacted}）。`
        : "尚未选择或载入本地工作区安全摘要。",
      nextAction: selectedProjectId || currentWorkspace ? "查看本地项目状态和安全路径摘要。" : "创建或打开一个本地项目。"
    },
    {
      title: "Local Privacy",
      cnTitle: "本地隐私",
      status: summary?.local_only || localConfigSummary?.local_only ? "ready" : "not checked",
      safeSummary: "本地优先：secrets、hidden facts、debug data 和 private content 不进入普通 UI、报告、备份、诊断或导出。",
      nextAction: "查看隐私说明；Settings 中不提供账号、云同步或在线市场设置。"
    },
    {
      title: "Providers",
      cnTitle: "模型服务",
      status: providerConfigured ? "ready" : "warning",
      safeSummary: providerConfigured
        ? "Provider 配置只以安全布尔值、api_key_env、secret_ref 或 local_secret_ref 表示。"
        : "可配置 api_key_env、secret_ref、local_secret_ref、mock、local_stub 或 local_http；不保存明文 Key。",
      nextAction: providerConfigured ? "需要时打开 Provider 设置并手动测试连接。" : "配置本地 ProviderProfile，不把明文 Key 写入 UI 或项目。"
    },
    {
      title: "Provider Models",
      cnTitle: "模型分配",
      status: "available",
      safeSummary: "模型读取、安全 ModelProfile metadata、能力警告和按模式分配都在 Provider Connectivity 中管理。",
      nextAction: "打开模型列表，读取或手动添加模型，并分配给 Novel、Tavern、World、Cross-Mode 和 Quality。"
    },
    {
      title: "Export",
      cnTitle: "导出",
      status: "ready",
      safeSummary: "导出默认过滤 API key、provider secrets、hidden refs、raw debug、raw prompts 和 mature/private 内容。",
      nextAction: "写入本地导出文件前，先看预览并显式确认。"
    },
    {
      title: "Debug",
      cnTitle: "Debug / 调试",
      status: debugEnabled ? "enabled" : "disabled",
      safeSummary: debugEnabled
        ? "Debug API 已开启；Debug 页面仍受 DebugGate 控制且只读。"
        : "Debug API is disabled / Debug API 未开启；普通 UI 只显示安全摘要。",
      nextAction: debugEnabled ? "需要排查问题时进入 QA / Debug，只读查看。" : "只有确实需要调试时，才在本地开启 ENABLE_DEBUG_API。"
    },
    {
      title: "Backup / Restore",
      cnTitle: "备份 / 恢复",
      status: "ready",
      safeSummary: "备份和恢复仅本地执行，先 dry-run，默认排除 secrets、debug raw data、logs、caches、databases 和 build outputs。",
      nextAction: "任何确认写入前，先运行备份 dry-run 或恢复预览。"
    },
    {
      title: "Diagnostics",
      cnTitle: "诊断",
      status: "ready",
      safeSummary: "诊断预览会显示包含 / 排除内容，并过滤 secrets、raw env、hidden/debug、mature/private、logs 和 raw provider responses。",
      nextAction: "创建脱敏诊断包前，先在本地预览。"
    },
    {
      title: "Mature Module",
      cnTitle: "Mature Module / 成人内容模块",
      status: "disabled by default",
      safeSummary: "Mature 默认关闭，必须 opt-in；mature/private 内容默认不进入普通 prompt、导出、备份或诊断。",
      nextAction: "任何本地开启前，先查看 Tavern Boundary / Mature Settings。"
    },
    {
      title: "UI Preferences",
      cnTitle: "UI Preferences / 界面偏好",
      status: "available",
      safeSummary: `快捷键${keyboardShortcutsEnabled ? "已开启" : "已关闭"}；Reduced Motion ${reducedMotionEnabled ? "已开启" : "已关闭"}。`,
      nextAction: "打开快捷键帮助，或调整 Reduced Motion 以提升长时间使用舒适度。"
    }
  ];

  return (
    <section className="studio-section" data-lazy-settings-privacy-panel="true">
      <div className="authoring-pane-header">
        <div>
          <h3>{promptLabOnly ? "Prompt Lab Privacy / 模型隐私" : "设置 / 隐私 / 模型服务"}</h3>
          <p className="muted">
            仅显示本地配置安全摘要。API Key、raw env、Provider secrets、raw prompts、hidden facts 和敏感本地路径都不会渲染。
          </p>
        </div>
        <StatusBadge label={summary?.local_only ? "本地优先" : "安全摘要未载入"} enabled={summary?.local_only} />
      </div>
      <ErrorPanel message={error} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="项目" value={selectedProjectId || "local_project"}>
          <p>{currentWorkspace ? `${currentWorkspace.name} (${currentWorkspace.path_redacted})` : "尚未选择工作区，或安全工作区摘要不可用。"}</p>
        </DashboardCard>
        <DashboardCard title="模型服务" value={summary?.llm_provider ?? localConfigSummary?.provider_type ?? "unknown"}>
          <p>{summary?.api_key_configured || localConfigSummary?.api_key_configured ? "API key 仅在后端配置；此处不显示值。" : "前端不显示也不保存 Key 值。"}</p>
        </DashboardCard>
        <DashboardCard title="最近项目" value={String(recentProjectCount)}>
          <p>最近项目只保存安全摘要。</p>
        </DashboardCard>
      </div>
      <SectionCard title="产品设置分区" description="v3.7 本地产品设置地图。这里只显示安全摘要，不写入密钥或 GameState。">
        <div className="settings-section-grid" role="list" aria-label="产品设置分区">
          {productSettingsSections.map((section) => (
            <article className="settings-section-item" role="listitem" key={section.title}>
              <div className="settings-section-heading">
                <h5>{section.cnTitle}</h5>
                <span className="sr-only">{section.title}</span>
                <span className="badge">{section.status}</span>
              </div>
              <p>{section.safeSummary}</p>
              <p className="muted">下一步：{section.nextAction}</p>
            </article>
          ))}
        </div>
        <p className="muted">不提供账号设置、云同步设置、在线市场设置或远程包下载设置；本页面只管理本地产品配置。</p>
      </SectionCard>
      <div className="studio-grid two-column-grid">
        <SectionCard title="本地配置" description="只显示安全本地摘要和脱敏路径提示。">
          <div className="button-row">
            <button type="button" onClick={onRefreshLocalConfig}>刷新配置</button>
            <button type="button" onClick={onGenerateLocalEnvTemplate}>生成 .env 示例</button>
          </div>
          {localConfigSummary ? (
            <ItemList
              emptyText="暂无配置摘要。"
              items={[
                `模型服务类型：${localConfigSummary.provider_type}`,
                `模型 ID：${localConfigSummary.model_id}`,
                `使用记录：${localConfigSummary.usage_tracking_enabled ? "已开启" : "已关闭"}`,
                `Debug API：${localConfigSummary.debug_api_enabled ? "已开启" : "已关闭"}`,
                `数据库：${localConfigSummary.database_configured ? "已配置" : "未配置"}`
              ].map((item) => <span>{item}</span>)}
            />
          ) : (
            <EmptyState title="尚未载入本地配置摘要。" detail="刷新本地配置后，会显示安全布尔值和脱敏路径提示。" />
          )}
          <ItemList
            emptyText="暂无配置问题。"
            items={localConfigIssues.map((issue) => (
              <span key={`${issue.code}-${issue.safe_field}`}>
                <QualitySeverityBadge severity={issue.severity} /> {issue.safe_field}: {issue.message}
              </span>
            ))}
          />
        </SectionCard>
        <SectionCard title="UI Preferences / 界面偏好" description="可访问性设置只影响本地 UI，不会改变世界状态。">
          <label>
            <input type="checkbox" checked={keyboardShortcutsEnabled} onChange={(event) => onToggleKeyboardShortcuts(event.target.checked)} />
            启用键盘快捷键
          </label>
          <label>
            <input type="checkbox" checked={reducedMotionEnabled} onChange={(event) => onToggleReducedMotion(event.target.checked)} />
            启用 Reduced Motion / 减少动画
          </label>
          <div className="button-row">
            <button type="button" onClick={onOpenShortcutHelp}>打开快捷键帮助</button>
            <button type="button" onClick={onClearRecentProjects}>清空最近项目</button>
          </div>
          <p className="muted">危险操作不会绑定到直接快捷键，仍然必须显式确认。</p>
        </SectionCard>
      </div>
      {localEnvTemplate ? (
        <SectionCard title=".env 示例预览" description="模板只包含占位符；不会生成或显示真实 Key。">
          <SafeJSON value={{ file_name: localEnvTemplate.file_name, contains_real_secret: localEnvTemplate.contains_real_secret, writes_to_disk: localEnvTemplate.writes_to_disk }} />
        </SectionCard>
      ) : null}
      <PromptProfileSafeSettings summary={summary} onSelectPromptProfile={onSelectPromptProfile} />
    </section>
  );
}

function ProviderProfileForm({
  draft,
  validationMessage,
  onChange,
  onSubmit
}: {
  draft: ProviderProfileDraft;
  validationMessage: string;
  onChange: (draft: ProviderProfileDraft) => void;
  onSubmit: (event: FormEvent) => void;
}) {
  const firstModel = draft.model_profiles[0] ?? { model_id: "", display_name: "", supports_json: false, supports_streaming: false, recommended_use_cases: [] };
  return (
    <form className="form-grid provider-profile-form" onSubmit={onSubmit}>
      <label>
        Profile ID / 配置 ID
        <input value={draft.provider_profile_id} onChange={(event) => onChange({ ...draft, provider_profile_id: event.target.value })} />
      </label>
      <label>
        显示名称
        <input value={draft.display_name} onChange={(event) => onChange({ ...draft, display_name: event.target.value })} />
      </label>
      <label>
        模型服务类型
        <select value={draft.provider_type} onChange={(event) => onChange({ ...draft, provider_type: event.target.value })}>
          <option value="local_stub">local_stub</option>
          <option value="mock">mock</option>
          <option value="local_http">local_http</option>
          <option value="openai">openai</option>
          <option value="openai_compatible">openai_compatible</option>
          <option value="relay">relay</option>
          <option value="custom">custom</option>
        </select>
      </label>
      <label>
        Base URL
        <input value={draft.base_url ?? ""} onChange={(event) => onChange({ ...draft, base_url: event.target.value })} placeholder="Optional endpoint URL" />
      </label>
      <label>
        Base URL 环境变量
        <input value={draft.base_url_env ?? ""} onChange={(event) => onChange({ ...draft, base_url_env: event.target.value })} placeholder="LOCAL_LLM_BASE_URL" />
      </label>
      <label>
        API Key 环境变量
        <input value={draft.api_key_env ?? ""} onChange={(event) => onChange({ ...draft, api_key_env: event.target.value })} placeholder="OPENAI_API_KEY" />
      </label>
      <label>
        Secret Ref / 本地密钥引用
        <input value={draft.secret_ref ?? ""} onChange={(event) => onChange({ ...draft, secret_ref: event.target.value })} placeholder="local-secret-id" />
      </label>
      <label>
        Local Secret Ref / 本地密钥引用
        <input value={draft.local_secret_ref ?? ""} onChange={(event) => onChange({ ...draft, local_secret_ref: event.target.value })} placeholder="providers/main" />
      </label>
      <label>
        Model ID / 模型 ID
        <input value={firstModel.model_id} onChange={(event) => onChange({ ...draft, model_profiles: [{ ...firstModel, model_id: event.target.value }] })} />
      </label>
      <label>
        超时秒数
        <input type="number" min={1} max={600} value={draft.default_timeout_seconds ?? 30} onChange={(event) => onChange({ ...draft, default_timeout_seconds: Number(event.target.value) || 30 })} />
      </label>
      <label>
        <input type="checkbox" checked={draft.enabled ?? true} onChange={(event) => onChange({ ...draft, enabled: event.target.checked })} />
        启用
      </label>
      <button type="submit">保存安全 Provider 配置</button>
      <p className="muted">{validationMessage || "This form intentionally has no plaintext API key field. 此表单没有明文 API key 字段，只保存 api_key_env / secret_ref / local_secret_ref / model metadata。"}</p>
    </form>
  );
}

function UsageGroupList({ title, emptyText, rows }: { title: string; emptyText: string; rows: CostLatencyGroupSummary[] }) {
  return (
    <SectionCard title={title} description="Safe usage summary only.">
      <ItemList
        emptyText={emptyText}
        items={rows.map((item) => (
          <span key={item.key}>
            {item.key}: {item.count} calls, {item.failures} errors, {item.total_tokens_estimated} tokens, cost {formatEstimatedCost(item.total_cost_estimated)}, p50 {formatDuration(item.latency_p50_ms)}
          </span>
        ))}
      />
    </SectionCard>
  );
}

function UsageUseCaseList({ rows }: { rows: ModelUsageSummary["by_use_case"] }) {
  return (
    <SectionCard title="By use case" description="Mode routing and task-level usage distribution.">
      <ItemList
        emptyText="No usage by use case."
        items={rows.map((item) => (
          <span key={item.use_case}>
            {item.use_case}: {item.count} calls, {item.failures} errors, input {item.total_input_tokens_estimated}, output {item.total_output_tokens_estimated}, cost {formatEstimatedCost(item.total_cost_estimated)}, avg {formatDuration(item.average_latency_ms)}
          </span>
        ))}
      />
    </SectionCard>
  );
}

function buildProviderConnectivityRow(profile: ProviderProfileSummary, status: Record<string, unknown> | undefined, lastTested: string | undefined): ProviderConnectivityRow {
  const statusValue = statusString(readStatusValue(status, "status") || (profile.enabled ? "configured_not_tested" : "unconfigured"));
  const latencyMs = typeof status?.latency_ms === "number" ? status.latency_ms : undefined;
  const safeErrorType = String(status?.safe_error_type ?? status?.error_type ?? "");
  const stale = Boolean(status?.stale) || String(status?.cache_state ?? "") === "stale";
  const warnings = [
    profile.enabled ? "" : "provider disabled",
    providerUsuallyNeedsSecret(profile.provider_type) && !profile.api_key_env && !profile.secret_ref && !profile.local_secret_ref ? "missing secret reference" : "",
    safeErrorType ? `safe error ${safeErrorType}` : "",
    stale ? "cached status is stale" : "",
    latencyMs && latencyMs > PROVIDER_HIGH_LATENCY_MS ? "high latency" : ""
  ].filter(Boolean);
  return {
    providerId: profile.provider_profile_id,
    displayName: profile.display_name,
    providerType: profile.provider_type,
    connectionStatus: statusValue,
    modelCount: profile.model_profiles.length,
    lastTestedTime: formatDateTime(lastTested || (typeof status?.tested_at === "string" ? status.tested_at : "")),
    cacheState: String(status?.cache_state ?? (stale ? "stale" : "fresh")),
    stale,
    latencyMs,
    latencyLabel: formatDuration(latencyMs),
    safeErrorType,
    allowedModes: profile.allowed_modes ?? [],
    defaultModel: profile.model_profiles[0]?.model_id ?? "not set",
    warnings
  };
}

function buildProviderModelListRows(profiles: ProviderProfileSummary[], matrix: ProviderModelCapabilityMatrix | null): ProviderModelListRow[] {
  const matrixByProviderModel = new Map((matrix?.rows ?? []).map((row) => [`${row.provider_profile_id}:${row.model_id}`, row]));
  return profiles.flatMap((profile) =>
    profile.model_profiles.map((model) => {
      const matrixRow = matrixByProviderModel.get(`${profile.provider_profile_id}:${model.model_id}`);
      const capabilities = matrixRow?.capabilities ?? {};
      const supportsText = Boolean(model.supports_text ?? capabilities.supports_text ?? true);
      const supportsJson = Boolean(model.supports_json ?? capabilities.supports_json ?? false);
      const supportsStreaming = Boolean(model.supports_streaming ?? capabilities.supports_streaming ?? false);
      const supportsTools = Boolean(model.supports_tools ?? capabilities.supports_tools ?? false);
      return {
        id: `${profile.provider_profile_id}:${model.model_id}`,
        providerId: profile.provider_profile_id,
        providerName: profile.display_name,
        providerType: profile.provider_type,
        modelId: model.model_id,
        displayName: model.display_name || model.model_id,
        enabled: model.enabled ?? profile.enabled,
        supportsText,
        supportsJson,
        supportsStreaming,
        supportsTools,
        recommendedUseCases: model.recommended_use_cases ?? matrixRow?.recommended_use_cases ?? [],
        warnings: [...(matrixRow?.warnings ?? []), ...(matrixRow?.disabled_reasons ?? [])]
      };
    })
  );
}

function buildSlowProviderWarnings(
  providerRows: ProviderConnectivityRow[],
  summary: ModelUsageSummary | null,
  usageByProvider: CostLatencyGroupSummary[],
  recentUsage: ModelUsageRecord[]
): SlowProviderWarning[] {
  const warnings: SlowProviderWarning[] = [];
  for (const row of providerRows) {
    if ((row.latencyMs ?? 0) > PROVIDER_HIGH_LATENCY_MS) {
      warnings.push({
        id: `${row.providerId}:latency`,
        kind: "high_latency",
        severity: "warning",
        source: row.displayName,
        safeSummary: `Last connection latency ${row.latencyLabel}.`,
        suggestedActions: SLOW_PROVIDER_SAFE_ACTIONS
      });
    }
    if (row.connectionStatus === "timeout") {
      warnings.push({
        id: `${row.providerId}:timeout`,
        kind: "repeated_timeout",
        severity: "failed",
        source: row.displayName,
        safeSummary: "Connection status reports timeout.",
        suggestedActions: SLOW_PROVIDER_SAFE_ACTIONS
      });
    }
  }
  for (const group of usageByProvider) {
    if (group.latency_p95_ms > PROVIDER_AVERAGE_LATENCY_WARNING_MS) {
      warnings.push({
        id: `${group.key}:usage-latency`,
        kind: "high_latency",
        severity: "warning",
        source: group.key,
        safeSummary: `p95 latency ${formatDuration(group.latency_p95_ms)} across local usage records.`,
        suggestedActions: SLOW_PROVIDER_SAFE_ACTIONS
      });
    }
    if (group.count > 0 && group.failures / group.count >= PROVIDER_HIGH_ERROR_RATE) {
      warnings.push({
        id: `${group.key}:error-rate`,
        kind: "high_error_rate",
        severity: "warning",
        source: group.key,
        safeSummary: `${group.failures} failures across ${group.count} calls.`,
        suggestedActions: SLOW_PROVIDER_SAFE_ACTIONS
      });
    }
  }
  const timeoutCount = recentUsage.filter((record) => String(record.error_type ?? "").toLowerCase().includes("timeout")).length;
  if (timeoutCount >= PROVIDER_TIMEOUT_REPEAT_COUNT) {
    warnings.push({
      id: "recent-timeouts",
      kind: "repeated_timeout",
      severity: "warning",
      source: "recent usage",
      safeSummary: `${timeoutCount} recent timeout-like records.`,
      suggestedActions: SLOW_PROVIDER_SAFE_ACTIONS
    });
  }
  if (summary && summary.error_rate >= PROVIDER_HIGH_ERROR_RATE) {
    warnings.push({
      id: "summary-error-rate",
      kind: "high_error_rate",
      severity: "warning",
      source: "usage summary",
      safeSummary: `${Math.round(summary.error_rate * 100)}% local error rate.`,
      suggestedActions: SLOW_PROVIDER_SAFE_ACTIONS
    });
  }
  return warnings;
}

function buildProviderCapabilityMatrixSafeSummary(matrix: ProviderModelCapabilityMatrix | null, profiles: ProviderProfileSummary[]): ProviderCapabilityMatrixSafeSummary {
  const providerById = new Map(profiles.map((profile) => [profile.provider_profile_id, profile]));
  const rows = (matrix?.rows ?? []).map((row) => {
    const profile = providerById.get(row.provider_profile_id);
    const capabilities = row.capabilities ?? {};
    return {
      id: `${row.provider_profile_id}:${row.model_id}`,
      providerId: row.provider_profile_id,
      providerName: profile?.display_name ?? row.provider_profile_id,
      modelId: row.model_id,
      supportsText: Boolean(capabilities.supports_text ?? true),
      supportsJson: Boolean(capabilities.supports_json ?? false),
      supportsStreaming: Boolean(capabilities.supports_streaming ?? false),
      supportsTools: Boolean(capabilities.supports_tools ?? false),
      recommendedUseCases: row.recommended_use_cases ?? [],
      warnings: row.warnings ?? [],
      disabledReasons: row.disabled_reasons ?? []
    };
  });
  const providerSummaries = Array.from(new Set(rows.map((row) => row.providerId))).map((providerId) => {
    const providerRows = rows.filter((row) => row.providerId === providerId);
    return {
      providerId,
      providerName: providerRows[0]?.providerName ?? providerId,
      rowCount: providerRows.length,
      warningCount: providerRows.reduce((count, row) => count + row.warnings.length, 0),
      blockerCount: providerRows.reduce((count, row) => count + row.disabledReasons.length, 0)
    };
  });
  return {
    generatedAt: matrix?.generated_at ?? "",
    rowCount: rows.length,
    providerCount: providerSummaries.length,
    warningCount: rows.reduce((count, row) => count + row.warnings.length, 0),
    blockerCount: rows.reduce((count, row) => count + row.disabledReasons.length, 0),
    providers: providerSummaries,
    useCases: Array.from(new Set(rows.flatMap((row) => row.recommendedUseCases))).sort(),
    rows
  };
}

function buildProviderModelListSafeCacheSummary(projectId: string, profiles: ProviderProfileSummary[], matrix: ProviderModelCapabilityMatrix | null): ProviderModelListSafeCacheSummary {
  return {
    project_id: projectId,
    provider_count: profiles.length,
    model_count: profiles.reduce((count, profile) => count + profile.model_profiles.length, 0),
    matrix_row_count: matrix?.rows.length ?? 0,
    generated_at: matrix?.generated_at ?? new Date().toISOString(),
    providers: profiles.map((profile) => ({
      provider_profile_id: profile.provider_profile_id,
      display_name: profile.display_name,
      provider_type: profile.provider_type,
      model_count: profile.model_profiles.length,
      enabled: profile.enabled
    }))
  };
}

function buildProviderStatusSafeCacheValue(profileId: string, status: Record<string, unknown>): Record<string, unknown> {
  return {
    provider_profile_id: profileId,
    status: statusString(readStatusValue(status, "status") || "configured_not_tested"),
    tested_at: typeof status.tested_at === "string" ? status.tested_at : new Date().toISOString(),
    latency_ms: typeof status.latency_ms === "number" ? status.latency_ms : null,
    safe_error_type: typeof status.safe_error_type === "string" ? status.safe_error_type : typeof status.error_type === "string" ? status.error_type : null,
    model_count: typeof status.model_count === "number" ? status.model_count : undefined,
    redaction_applied: Boolean(status.redaction_applied ?? true),
    age_seconds: typeof status.age_seconds === "number" ? status.age_seconds : undefined,
    ttl_seconds: typeof status.ttl_seconds === "number" ? status.ttl_seconds : undefined,
    stale: Boolean(status.stale),
    cache_state: typeof status.cache_state === "string" ? status.cache_state : undefined
  };
}

function providerModelListCacheKey(projectId: string): string {
  return `v36:provider-model-list:${projectId}`;
}

function providerStatusCacheKey(projectId: string, profileId: string): string {
  return `v36:provider-status:${projectId}:${profileId}`;
}

function modelRowSupports(row: ProviderModelListRow, filter: ProviderModelCapabilityFilter): boolean {
  if (filter === "supports_text") return row.supportsText;
  if (filter === "supports_json") return row.supportsJson;
  if (filter === "supports_streaming") return row.supportsStreaming;
  if (filter === "supports_tools") return row.supportsTools;
  return true;
}

function capabilityMatrixRowSupports(row: ProviderCapabilityMatrixSafeRow, filter: ProviderCapabilityMatrixFilter): boolean {
  if (filter === "supports_text") return row.supportsText;
  if (filter === "supports_json") return row.supportsJson;
  if (filter === "supports_streaming") return row.supportsStreaming;
  if (filter === "supports_tools") return row.supportsTools;
  return true;
}

function routingUseCaseRequiresJson(useCase: ProviderRoutingUseCase): boolean {
  return ["world_intent_parse", "structured_json", "cross_mode_draft", "quality_eval", "memory_summary"].includes(useCase);
}

function providerUseCaseLabel(useCase: string): string {
  return PROVIDER_MODEL_ASSIGNMENT_USE_CASES.find((item) => item.value === useCase)?.label ?? useCase;
}

function buildDefaultRoutingRule(
  useCase: ProviderRoutingUseCase,
  primaryProviderId: string,
  primaryModelId: string,
  fallbackProviderId: string,
  fallbackModelId: string
): ProviderRoutingRule {
  return {
    use_case: useCase,
    primary_provider_id: primaryProviderId || "local_stub",
    primary_model_id: primaryModelId || "local_stub",
    fallback_provider_id: fallbackProviderId || null,
    fallback_model_id: fallbackModelId || null,
    require_json_support: routingUseCaseRequiresJson(useCase),
    require_local_only: false,
    enabled: true
  };
}

function findProviderModel(profiles: ProviderProfileSummary[], providerId: string, modelId: string): ProviderProfileSummary["model_profiles"][number] | undefined {
  return profiles.find((profile) => profile.provider_profile_id === providerId)?.model_profiles.find((model) => model.model_id === modelId);
}

function providerUsuallyNeedsSecret(providerType: string): boolean {
  return ["openai", "openai_compatible", "relay", "custom"].includes(providerType);
}

function inferSecretMode(draft: ProviderProfileDraft): ProviderSecretInputMode {
  if (draft.api_key_env) return "api_key_env";
  if (draft.secret_ref) return "secret_ref";
  if (draft.local_secret_ref) return "local_secret_ref";
  if (providerUsuallyNeedsSecret(draft.provider_type)) return "api_key_env";
  return "none";
}

function providerStatusToChinese(status: string, safeMessage = ""): string {
  const labels: Record<string, string> = {
    unconfigured: "未配置",
    configured_not_tested: "已配置，未测试",
    connected: "连接成功",
    disconnected: "未连接",
    missing_secret: "缺少 API key",
    invalid_base_url: "Base URL 无效",
    auth_failed: "认证失败",
    model_list_failed: "模型列表读取失败",
    unsupported_model_list: "Provider 不支持模型列表",
    timeout: "超时"
  };
  const label = labels[status] ?? status;
  return safeMessage ? `${label}：${safeMessage}` : label;
}

function providerReportStatusToChinese(status: string, safeMessage = ""): string {
  if (status === "ok") {
    return safeMessage ? `读取成功：${safeMessage}` : "读取成功";
  }
  return providerStatusToChinese(status, safeMessage);
}

function modelOptionsForProvider(profiles: ProviderProfileSummary[], providerId: string, currentModelId: string): string[] {
  const profile = profiles.find((item) => item.provider_profile_id === providerId);
  const options = new Set(profile?.model_profiles.map((model) => model.model_id).filter(Boolean) ?? []);
  if (currentModelId) options.add(currentModelId);
  if (options.size === 0) options.add(providerId || "local_stub");
  return Array.from(options);
}

function statusString(value: unknown): ProviderConnectivityStatus {
  const status = String(value || "configured_not_tested");
  if (
    status === "unconfigured" ||
    status === "configured_not_tested" ||
    status === "connected" ||
    status === "disconnected" ||
    status === "missing_secret" ||
    status === "invalid_base_url" ||
    status === "auth_failed" ||
    status === "model_list_failed" ||
    status === "unsupported_model_list" ||
    status === "timeout"
  ) {
    return status;
  }
  return "configured_not_tested";
}

function readStatusValue(status: Record<string, unknown> | undefined, key: string): unknown {
  if (!status) return undefined;
  return status[key];
}

function formatEstimatedCost(value: number): string {
  return `$${value.toFixed(value > 0 && value < 0.01 ? 6 : 4)}`;
}

function formatDuration(value: number | undefined): string {
  if (value === undefined || Number.isNaN(value)) return "n/a";
  if (value < 1000) return `${Math.round(value)} ms`;
  return `${(value / 1000).toFixed(1)} s`;
}

function formatDateTime(value: string): string {
  if (!value) return "not tested";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function motionSafeScrollBehavior(): ScrollBehavior {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
  } catch {
    return "auto";
  }
}

function providerChecklistItemClass(status: string): string {
  if (status === "pass") return "ready";
  if (status === "warning") return "warning";
  return "missing";
}

function providerChecklistPillClass(status: string): string {
  if (status === "pass") return "pass";
  if (status === "warning") return "warning";
  return "error";
}

function redactProviderChecklistText(value: string): string {
  return value
    .replace(/sk-[A-Za-z0-9_-]{12,}/g, "[redacted-key]")
    .replace(/Authorization\s*:\s*Bearer\s+\S+/gi, "Authorization: [redacted]")
    .replace(/api[_ -]?key\s*[:=]\s*\S+/gi, "api key: [redacted]")
    .replace(/secret[_ -]?ref\s*[:=]\s*\S+/gi, "secret ref: [redacted]");
}

function toErrorMessage(error: unknown): string {
  return getErrorMessageSafe(error);
}

function DashboardCard({ title, value, children }: { title: string; value: string; children?: ReactNode }) {
  return (
    <article className="dashboard-card">
      <span className="dashboard-card-title">{title}</span>
      <strong>{value}</strong>
      {children}
    </article>
  );
}

function SectionCard({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return (
    <section className="section-card">
      <h4>{title}</h4>
      {description ? <p className="muted">{description}</p> : null}
      {children}
    </section>
  );
}

function ErrorPanel({
  message,
  compact = false,
  suggestion = "建议：重试本地操作，检查模型服务设置，并使用 api_key_env、secret_ref 或 local_secret_ref 处理缺失密钥。"
}: {
  message: string;
  compact?: boolean;
  suggestion?: string;
}) {
  if (!message) return null;
  return (
    <div className={compact ? "error-panel compact" : "error-panel"} role="alert">
      <strong>请求失败</strong>
      <p>{toErrorMessage(message)}</p>
      <p className="muted">{suggestion}</p>
      <span className="sr-only">Suggested fix: retry the local action, check provider setup, and use api_key_env or secret_ref for missing secrets.</span>
    </div>
  );
}

function localizeProviderEmptyText(value?: string): string | undefined {
  if (!value) return value;
  if (/missing secret|api_key_env|secret_ref|provider/i.test(value)) {
    return "缺少模型服务配置。下一步：选择 Provider 类型，并使用 api_key_env、secret_ref 或 local_secret_ref。";
  }
  if (/model|models/i.test(value)) {
    return "暂无模型列表。下一步：手动读取模型列表，或手动添加 model_id。";
  }
  if (/No|Empty|Missing|Unavailable/i.test(value)) {
    return "暂无可显示内容。下一步：检查模型服务配置或返回首页继续设置。";
  }
  return value;
}

function EmptyState({ title, detail }: { title: string; detail?: string }) {
  const localizedTitle = localizeProviderEmptyText(title) ?? title;
  const localizedDetail = localizeProviderEmptyText(detail) ?? "下一步：配置模型服务、测试连接，或手动添加模型。";
  const displayTitle = /^(No|Empty|Missing|Unavailable)\b/i.test(title) ? `暂无内容：${localizedTitle}` : localizedTitle;
  return (
    <div className="empty-state">
      <strong>{displayTitle}</strong>
      <p>{localizedDetail}</p>
    </div>
  );
}

function FeatureCard({ title, detail }: { title: string; detail: string }) {
  return (
    <article className="feature-card">
      <h4>{title}</h4>
      <p>{detail}</p>
    </article>
  );
}

function ItemList({ items, emptyText }: { items: ReactNode[]; emptyText: string }) {
  if (!items.length) return <p className="muted">{emptyText}</p>;
  return (
    <ul className="compact-list">
      {items.map((item, index) => <li key={index}>{item}</li>)}
    </ul>
  );
}

function SafeJSON({ value }: { value: unknown }) {
  return (
    <pre className="safe-json" aria-label="Safe redacted JSON summary">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function StatusBadge({ label, enabled }: { label: string; enabled: boolean | undefined }) {
  return <span className={`status-badge ${enabled ? "status-ok" : "status-disabled"}`}>{label}</span>;
}

function ProviderConnectionStatusBadge({ status }: { status: string }) {
  const normalized = status === "connected" ? "ok" : status === "configured_not_tested" ? "warning" : "blocked";
  return <span className={`badge provider-status-${normalized}`}>{status}</span>;
}

function ModelCapabilityBadge({ label, supported }: { label: string; supported: boolean }) {
  return <span className={`badge capability-${supported ? "supported" : "missing"}`} aria-label={`${label} ${supported ? "supported" : "not supported"}`}>{label}: {supported ? "yes" : "no"}</span>;
}

function QualitySeverityBadge({ severity }: { severity: string }) {
  return <span className={`badge severity-${severity}`}>{severity}</span>;
}

function FilterToolbar({ children }: { children: ReactNode }) {
  return <div className="filter-toolbar" role="search">{children}</div>;
}

function SafeApiCacheStatusPanel({ status, onRefresh }: { status: SafeApiCacheStatus | null; onRefresh?: () => void }) {
  if (!status) {
    return (
      <div className="safe-cache-status">
        <strong>No cache entry yet.</strong>
        <p className="muted">Manual refresh will populate safe summaries only.</p>
        {onRefresh ? <button type="button" onClick={onRefresh}>Refresh</button> : null}
      </div>
    );
  }
  return (
    <div className={`safe-cache-status ${status.stale ? "stale" : "fresh"}`}>
      <strong>{status.label}</strong>
      <p className="muted">{status.summary}</p>
      <p className="muted">Updated {formatDateTime(status.updatedAt)}; stale {formatDateTime(status.staleAt)}{status.failed ? "; last refresh failed" : ""}</p>
      {status.safeError ? <p className="muted">{status.safeError}</p> : null}
      {onRefresh ? <button type="button" onClick={onRefresh}>Manual refresh</button> : null}
    </div>
  );
}
