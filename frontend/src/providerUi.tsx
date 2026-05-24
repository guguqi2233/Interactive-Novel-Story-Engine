import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
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
  fetchProjectProviderModelAssignments,
  fetchProjectProviderStatus,
  fetchProjectProviderUsageByMode,
  fetchProjectProviderUsageByProvider,
  fetchProjectProviderUsageRecent,
  fetchProjectProviderUsageSummary,
  fetchProjectProviders,
  fetchProviderCapabilities,
  fetchRecentModelUsage,
  getErrorMessageSafe,
  reviewPromptDiff,
  runLocalModelDiagnostics,
  runPromptRegressionSuite,
  runProviderBenchmark,
  runStructuredOutputReliability,
  saveProjectProviderModelAssignments,
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
const SLOW_PROVIDER_SAFE_ACTIONS = [
  "check base URL",
  "check local model service",
  "check provider status",
  "use another model/fallback",
  "increase timeout cautiously"
];

const PROVIDER_MODEL_ASSIGNMENT_USE_CASES: Array<{ value: ProviderRoutingUseCase; label: string }> = [
  { value: "novel_draft", label: "Novel draft" },
  { value: "novel_rewrite", label: "Novel rewrite" },
  { value: "tavern_reply", label: "Tavern reply" },
  { value: "multi_npc_reply", label: "Multi-NPC reply" },
  { value: "world_intent_parse", label: "World intent parser" },
  { value: "world_narration", label: "World narrator" },
  { value: "memory_summary", label: "Memory summary" },
  { value: "cross_mode_draft", label: "Cross-Mode draft" },
  { value: "structured_json", label: "Structured JSON" },
  { value: "quality_eval", label: "Quality eval" },
  { value: "cheap_summary", label: "Cheap summary" }
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

  async function saveProviderProfile(event: FormEvent) {
    event.preventDefault();
    const cleaned: ProviderProfileDraft = {
      ...providerDraft,
      base_url: providerDraft.base_url?.trim() || null,
      base_url_env: providerDraft.base_url_env?.trim() || null,
      api_key_env: providerDraft.api_key_env?.trim() || null,
      secret_ref: providerDraft.secret_ref?.trim() || null,
      allowed_modes: providerDraft.allowed_modes ?? [],
      model_profiles: providerDraft.model_profiles
        .filter((model) => model.model_id.trim())
        .map((model) => ({
          ...model,
          model_id: model.model_id.trim(),
          display_name: model.display_name?.trim() || model.model_id.trim(),
          recommended_use_cases: model.recommended_use_cases ?? []
        }))
    };
    const created = await createProjectProvider(projectId, cleaned);
    setProviderProfiles((current) => [...current.filter((item) => item.provider_profile_id !== created.provider.provider_profile_id), created.provider]);
    setProviderValidation("Profile saved. Secrets are still resolved only on the backend from env or local secret refs.");
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
    } catch (err) {
      markSafeApiCacheFailed(cacheKey, `Provider status safe summary: ${profileId}`, "provider", err);
      syncProviderSafeCacheStatuses();
      throw err;
    }
  }

  const profiles = summary?.prompt_profiles ?? [];
  const leftProfile = profiles[0] ? { id: profiles[0].id, hidden_fact_policy: "deny", state_modification_policy: "deny" } : {};
  const rightProfile = profiles[1] ? { id: profiles[1].id, hidden_fact_policy: "deny", state_modification_policy: "deny" } : leftProfile;

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
            <h4>Provider Profiles</h4>
            <p className="muted">API keys are never entered here; use env vars or local secret refs only.</p>
          </div>
          <button type="button" onClick={() => void runLabAction(() => loadProviderProfiles(true))}>
            Load Profiles
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
                Validate
              </button>
              <button type="button" onClick={() => void runLabAction(async () => loadProviderStatus(profile.provider_profile_id, true))}>
                Status
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

  return (
    <section className="studio-section provider-connectivity-dashboard" data-large-provider-model-list="windowed">
      <div className="authoring-pane-header">
        <div>
          <h4>Provider Connectivity Dashboard</h4>
          <p className="muted">Local provider status, safe model metadata, stale cache warnings, and routing health. API keys and raw provider responses are excluded.</p>
        </div>
        <div className="button-row">
          <button type="button" onClick={onFetchModels} disabled={isLoading}>
            {isLoading ? "Loading..." : "Fetch Models"}
          </button>
          <button type="button" onClick={onRefreshModels}>Refresh Models</button>
          <button type="button" onClick={onOpenModelAssignment}>Open Model Assignment</button>
          <button type="button" onClick={onOpenProviderSetup}>Open Provider Setup</button>
        </div>
      </div>
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Providers" value={String(profiles.length)}>
          <p>{profiles.length ? "Provider profiles loaded from local project metadata." : "No providers loaded. Fetch models or open setup."}</p>
        </DashboardCard>
        <DashboardCard title="Models" value={String(modelRows.length)}>
          <p>{filteredModelRows.length} visible after filters; only {visibleModels.length} rows are rendered in the DOM window.</p>
        </DashboardCard>
        <DashboardCard title="Warnings" value={String(slowWarnings.length)}>
          <p>Slow provider hints are safe summaries and never include prompt/output text.</p>
        </DashboardCard>
      </div>
      <div className="studio-grid two-column-grid">
        <SectionCard title="Provider List" description="Connection status cache is local and stores only safe metadata.">
          <ItemList
            emptyText="Provider list is empty."
            items={providerRows.map((row) => (
              <span key={row.providerId}>
                <ProviderConnectionStatusBadge status={row.connectionStatus} /> {row.displayName} ({row.providerType}) - {row.modelCount} models - {row.lastTestedTime}
                {row.stale ? " - stale" : ""} - {row.warnings.join("; ") || "no warnings"}
                <button type="button" onClick={() => onTestConnection(row.providerId)}>Test connection</button>
              </span>
            ))}
          />
        </SectionCard>
        <SectionCard title="Safe Cache" description="Manual refresh is available; stale entries do not auto-call providers.">
          {cacheStatuses.length ? (
            cacheStatuses.map((status) => <SafeApiCacheStatusPanel key={status.key} status={status} onRefresh={onRefreshModels} />)
          ) : (
            <SafeApiCacheStatusPanel status={null} onRefresh={onRefreshModels} />
          )}
        </SectionCard>
      </div>
      {slowWarnings.length ? (
        <SectionCard title="Slow Provider Warnings" description="No raw provider error, prompt, output, API key, or Authorization header is displayed.">
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
      <FilterToolbar>
        <label>
          Search models
          <input value={modelSearch} onChange={(event) => setModelSearch(event.target.value)} placeholder="provider, model, use case" />
        </label>
        <label>
          Capability
          <select value={capabilityFilter} onChange={(event) => setCapabilityFilter(event.target.value as ProviderModelCapabilityFilter)}>
            <option value="all">All capabilities</option>
            <option value="supports_text">supports_text</option>
            <option value="supports_json">supports_json</option>
            <option value="supports_streaming">supports_streaming</option>
            <option value="supports_tools">supports_tools</option>
          </select>
        </label>
        <label>
          Enabled
          <select value={enabledFilter} onChange={(event) => setEnabledFilter(event.target.value as ProviderModelEnabledFilter)}>
            <option value="all">Enabled and disabled</option>
            <option value="enabled">Enabled only</option>
            <option value="disabled">Disabled only</option>
          </select>
        </label>
        <label>
          Use case
          <select value={useCaseFilter} onChange={(event) => setUseCaseFilter(event.target.value)}>
            <option value="all">All use cases</option>
            {recommendedUseCases.map((useCase) => (
              <option key={useCase} value={useCase}>{useCase}</option>
            ))}
          </select>
        </label>
      </FilterToolbar>
      <div className="section-heading-row">
        <p className="muted">
          Rendering {filteredModelRows.length ? modelWindowStart + 1 : 0}-{Math.min(modelWindowStart + visibleModels.length, filteredModelRows.length)} of {filteredModelRows.length} filtered model rows.
        </p>
        <div className="pagination-controls" aria-label="Provider model list pagination">
          <button type="button" onClick={() => setModelPage(0)} disabled={clampedModelPage === 0}>First</button>
          <button type="button" onClick={() => setModelPage(Math.max(clampedModelPage - 1, 0))} disabled={clampedModelPage === 0}>Previous</button>
          <span>Page {clampedModelPage + 1} / {modelPageCount}</span>
          <button type="button" onClick={() => setModelPage(Math.min(clampedModelPage + 1, modelPageCount - 1))} disabled={clampedModelPage >= modelPageCount - 1}>Next</button>
          <button type="button" onClick={() => setModelPage(modelPageCount - 1)} disabled={clampedModelPage >= modelPageCount - 1}>Last</button>
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
              <ModelCapabilityBadge label="text" supported={row.supportsText} />
              <ModelCapabilityBadge label="json" supported={row.supportsJson} />
              <ModelCapabilityBadge label="streaming" supported={row.supportsStreaming} />
              <ModelCapabilityBadge label="tools" supported={row.supportsTools} />
            </div>
            <p className="muted">{row.recommendedUseCases.join(", ") || "No recommended use cases."}</p>
            <p className="muted">{row.warnings.join("; ") || "No warnings."}</p>
          </article>
        )) : (
          <EmptyState title="No provider models match these filters." detail="Try clearing search or capability filters. Raw provider responses are never rendered." />
        )}
      </div>
      {modelAssignmentOpen ? <ProviderModelAssignmentPanel projectId={projectId} profiles={profiles} /> : null}
    </section>
  );
}

function ProviderModelAssignmentPanel({ projectId, profiles }: { projectId: string; profiles: ProviderProfileSummary[] }) {
  const [summary, setSummary] = useState<ProjectProviderModelAssignmentSummary | null>(null);
  const [message, setMessage] = useState("");
  const [useCase, setUseCase] = useState<ProviderRoutingUseCase>("world_intent_parse");
  const [primaryProviderId, setPrimaryProviderId] = useState(profiles[0]?.provider_profile_id ?? "local_stub");
  const [primaryModelId, setPrimaryModelId] = useState(profiles[0]?.model_profiles[0]?.model_id ?? "local_stub");
  const [fallbackProviderId, setFallbackProviderId] = useState("mock");
  const [fallbackModelId, setFallbackModelId] = useState("mock");
  const [requireJson, setRequireJson] = useState(true);
  const [requireLocalOnly, setRequireLocalOnly] = useState(false);

  const providerOptions = useMemo(() => Array.from(new Set([...profiles.map((profile) => profile.provider_profile_id), primaryProviderId, fallbackProviderId])).filter(Boolean), [fallbackProviderId, primaryProviderId, profiles]);
  const primaryModelOptions = useMemo(() => modelOptionsForProvider(profiles, primaryProviderId, primaryModelId), [primaryModelId, primaryProviderId, profiles]);
  const fallbackModelOptions = useMemo(() => modelOptionsForProvider(profiles, fallbackProviderId, fallbackModelId), [fallbackModelId, fallbackProviderId, profiles]);
  const currentRule = useMemo<ProviderRoutingRule>(() => ({
    use_case: useCase,
    primary_provider_id: primaryProviderId,
    primary_model_id: primaryModelId,
    fallback_provider_id: fallbackProviderId || null,
    fallback_model_id: fallbackModelId || null,
    require_json_support: requireJson || routingUseCaseRequiresJson(useCase),
    require_local_only: requireLocalOnly,
    enabled: true
  }), [fallbackModelId, fallbackProviderId, primaryModelId, primaryProviderId, requireJson, requireLocalOnly, useCase]);
  const currentConfig = useMemo<ProviderRoutingConfig>(() => {
    const existing = (summary?.rules ?? []).filter((rule) => rule.use_case !== useCase);
    return { rules: [...existing, currentRule] };
  }, [currentRule, summary?.rules, useCase]);

  async function run(action: () => Promise<void>) {
    setMessage("");
    try {
      await action();
    } catch (error) {
      setMessage(toErrorMessage(error));
    }
  }

  return (
    <section className="studio-section model-assignment-panel">
      <div className="authoring-pane-header">
        <div>
          <h4>Provider Model Assignment by Mode</h4>
          <p className="muted">Assign provider/model metadata for local modes. Provider Gateway remains the only runtime model entry.</p>
        </div>
        <div className="button-row">
          <button type="button" onClick={() => void run(async () => setSummary(await fetchProjectProviderModelAssignments(projectId)))}>
            Load Assignments
          </button>
          <button type="button" onClick={() => void run(async () => setSummary(await validateProjectProviderModelAssignments(projectId, currentConfig)))}>
            Validate Routing
          </button>
          <button type="button" onClick={() => void run(async () => {
            setSummary(await saveProjectProviderModelAssignments(projectId, currentConfig));
            setMessage("Model assignment saved. No API key or provider secret was stored.");
          })}>
            Save Assignment
          </button>
        </div>
      </div>
      <ErrorPanel message={message} compact />
      <div className="form-grid">
        <label>
          Use case
          <select value={useCase} onChange={(event) => setUseCase(event.target.value as ProviderRoutingUseCase)}>
            {PROVIDER_MODEL_ASSIGNMENT_USE_CASES.map((item) => (
              <option key={item.value} value={item.value}>{item.label}</option>
            ))}
          </select>
        </label>
        <label>
          Primary provider
          <select value={primaryProviderId} onChange={(event) => setPrimaryProviderId(event.target.value)}>
            {providerOptions.map((providerId) => <option key={providerId} value={providerId}>{providerId}</option>)}
          </select>
        </label>
        <label>
          Primary model
          <select value={primaryModelId} onChange={(event) => setPrimaryModelId(event.target.value)}>
            {primaryModelOptions.map((modelId) => <option key={modelId} value={modelId}>{modelId}</option>)}
          </select>
        </label>
        <label>
          Fallback provider
          <select value={fallbackProviderId} onChange={(event) => setFallbackProviderId(event.target.value)}>
            {providerOptions.map((providerId) => <option key={providerId} value={providerId}>{providerId}</option>)}
          </select>
        </label>
        <label>
          Fallback model
          <select value={fallbackModelId} onChange={(event) => setFallbackModelId(event.target.value)}>
            {fallbackModelOptions.map((modelId) => <option key={modelId} value={modelId}>{modelId}</option>)}
          </select>
        </label>
        <label>
          <input type="checkbox" checked={requireJson || routingUseCaseRequiresJson(useCase)} onChange={(event) => setRequireJson(event.target.checked)} />
          Require JSON capability
        </label>
        <label>
          <input type="checkbox" checked={requireLocalOnly} onChange={(event) => setRequireLocalOnly(event.target.checked)} />
          Require local-only provider
        </label>
      </div>
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="JSON Warning" value={routingUseCaseRequiresJson(useCase) ? "required" : "optional"}>
          <p>World intent parser, structured JSON, quality eval, memory summary, and cross-mode draft assignments need JSON-capable models.</p>
        </DashboardCard>
        <DashboardCard title="Fallback" value={fallbackProviderId ? "configured" : "none"}>
          <p>Fallback chains are metadata only and do not trigger provider calls.</p>
        </DashboardCard>
        <DashboardCard title="Validation" value={summary?.validation_reports.every((report) => report.ok) ? "ok" : summary ? "warnings" : "not loaded"}>
          <p>{summary?.warnings.join(", ") || "Load or validate assignments to see safe warnings."}</p>
        </DashboardCard>
      </div>
      {summary ? (
        <ItemList
          emptyText="No model assignments."
          items={summary.rules.map((rule) => (
            <span key={`${rule.use_case}-${rule.primary_provider_id}-${rule.primary_model_id}`}>
              {rule.use_case}: {rule.primary_provider_id}/{rule.primary_model_id}
              {rule.fallback_provider_id ? ` -> ${rule.fallback_provider_id}/${rule.fallback_model_id}` : ""}
              {summary.validation_reports.find((report) => report.rule.use_case === rule.use_case)?.warnings.length
                ? ` (${summary.validation_reports.find((report) => report.rule.use_case === rule.use_case)?.warnings.join(", ")})`
                : ""}
            </span>
          ))}
        />
      ) : (
        <EmptyState title="No assignments loaded." detail="Load or validate local model assignments. Secrets are not part of routing metadata." />
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
          <h4>Prompt Profile Safe Settings</h4>
          <p className="muted">Prompt profile selection is local metadata. No raw prompt, API key, hidden facts, or provider secret is shown.</p>
        </div>
        <StatusBadge label={summary?.local_only ? "local-only" : "summary unavailable"} enabled={summary?.local_only} />
      </div>
      {summary ? (
        <>
          <div className="form-grid">
            <label>
              Selected prompt profile
              <select value={selectedProfileId} onChange={(event) => setSelectedProfileId(event.target.value)}>
                <option value="">Select a profile</option>
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
              Select Profile
            </button>
          </div>
          <div className="studio-columns">
            <section>
              <h4>Privacy Notes</h4>
              <ul className="compact-list">
                {summary.privacy_notes.map((note) => <li key={note}>{note}</li>)}
              </ul>
            </section>
            <section>
              <h4>Boundaries</h4>
              <ul className="compact-list">
                <li>Provider Gateway remains the only model entry.</li>
                <li>API keys stay in env vars or local secret refs.</li>
                <li>Provider connectivity is local configuration, not an online platform.</li>
                <li>World facts remain governed by the World Engine.</li>
              </ul>
            </section>
          </div>
        </>
      ) : (
        <EmptyState title="Config summary unavailable." detail="The prompt settings page stays empty if the safe summary endpoint fails." />
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
  return (
    <section className="studio-section" data-lazy-settings-privacy-panel="true">
      <div className="authoring-pane-header">
        <div>
          <h3>{promptLabOnly ? "Prompt Lab Privacy" : "Settings / Privacy"}</h3>
          <p className="muted">
            Local configuration summary only. API keys, raw env, provider secrets, raw prompts, hidden facts, and sensitive local paths are not rendered.
          </p>
        </div>
        <StatusBadge label={summary?.local_only ? "local-only" : "summary unavailable"} enabled={summary?.local_only} />
      </div>
      <ErrorPanel message={error} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Project" value={selectedProjectId || "local_project"}>
          <p>{currentWorkspace ? `${currentWorkspace.name} (${currentWorkspace.path_redacted})` : "No workspace selected or safe workspace summary unavailable."}</p>
        </DashboardCard>
        <DashboardCard title="Provider" value={summary?.llm_provider ?? localConfigSummary?.provider_type ?? "unknown"}>
          <p>{summary?.api_key_configured || localConfigSummary?.api_key_configured ? "API key is configured on backend only; value is not shown." : "No key value displayed or stored in frontend."}</p>
        </DashboardCard>
        <DashboardCard title="Recent Projects" value={String(recentProjectCount)}>
          <p>Recent project entries store safe summaries only.</p>
        </DashboardCard>
      </div>
      <div className="studio-grid two-column-grid">
        <SectionCard title="Local Config" description="Safe local summary with redacted path hints.">
          <div className="button-row">
            <button type="button" onClick={onRefreshLocalConfig}>Refresh Config</button>
            <button type="button" onClick={onGenerateLocalEnvTemplate}>Generate .env Example</button>
          </div>
          {localConfigSummary ? (
            <ItemList
              emptyText="No config rows."
              items={[
                `Provider type: ${localConfigSummary.provider_type}`,
                `Model id: ${localConfigSummary.model_id}`,
                `Usage tracking: ${localConfigSummary.usage_tracking_enabled ? "enabled" : "disabled"}`,
                `Debug API: ${localConfigSummary.debug_api_enabled ? "enabled" : "disabled"}`,
                `Database: ${localConfigSummary.database_configured ? "configured" : "not configured"}`
              ].map((item) => <span>{item}</span>)}
            />
          ) : (
            <EmptyState title="Local config summary not loaded." detail="Refresh local config to show safe booleans and redacted path hints." />
          )}
          <ItemList
            emptyText="No config issues."
            items={localConfigIssues.map((issue) => (
              <span key={`${issue.code}-${issue.safe_field}`}>
                <QualitySeverityBadge severity={issue.severity} /> {issue.safe_field}: {issue.message}
              </span>
            ))}
          />
        </SectionCard>
        <SectionCard title="Local UI Preferences" description="Accessibility settings are local UI preferences and never apply world changes.">
          <label>
            <input type="checkbox" checked={keyboardShortcutsEnabled} onChange={(event) => onToggleKeyboardShortcuts(event.target.checked)} />
            Keyboard shortcuts enabled
          </label>
          <label>
            <input type="checkbox" checked={reducedMotionEnabled} onChange={(event) => onToggleReducedMotion(event.target.checked)} />
            Reduced motion enabled
          </label>
          <div className="button-row">
            <button type="button" onClick={onOpenShortcutHelp}>Open Shortcut Help</button>
            <button type="button" onClick={onClearRecentProjects}>Clear Recent Projects</button>
          </div>
          <p className="muted">Dangerous actions are never bound to direct shortcuts and still require confirm.</p>
        </SectionCard>
      </div>
      {localEnvTemplate ? (
        <SectionCard title=".env Example Preview" description="Template preview is placeholder-only; no real key is generated or shown.">
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
        Profile ID
        <input value={draft.provider_profile_id} onChange={(event) => onChange({ ...draft, provider_profile_id: event.target.value })} />
      </label>
      <label>
        Display Name
        <input value={draft.display_name} onChange={(event) => onChange({ ...draft, display_name: event.target.value })} />
      </label>
      <label>
        Provider Type
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
        Base URL Env
        <input value={draft.base_url_env ?? ""} onChange={(event) => onChange({ ...draft, base_url_env: event.target.value })} placeholder="LOCAL_LLM_BASE_URL" />
      </label>
      <label>
        API Key Env
        <input value={draft.api_key_env ?? ""} onChange={(event) => onChange({ ...draft, api_key_env: event.target.value })} placeholder="OPENAI_API_KEY" />
      </label>
      <label>
        Secret Ref
        <input value={draft.secret_ref ?? ""} onChange={(event) => onChange({ ...draft, secret_ref: event.target.value })} placeholder="local-secret-id" />
      </label>
      <label>
        Model ID
        <input value={firstModel.model_id} onChange={(event) => onChange({ ...draft, model_profiles: [{ ...firstModel, model_id: event.target.value }] })} />
      </label>
      <label>
        Timeout Seconds
        <input type="number" min={1} max={600} value={draft.default_timeout_seconds ?? 30} onChange={(event) => onChange({ ...draft, default_timeout_seconds: Number(event.target.value) || 30 })} />
      </label>
      <label>
        <input type="checkbox" checked={draft.enabled ?? true} onChange={(event) => onChange({ ...draft, enabled: event.target.checked })} />
        Enabled
      </label>
      <button type="submit">Save Safe Profile</button>
      <p className="muted">{validationMessage || "This form intentionally has no plaintext API key field."}</p>
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
    providerUsuallyNeedsSecret(profile.provider_type) && !profile.api_key_env && !profile.secret_ref ? "missing secret reference" : "",
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

function providerUsuallyNeedsSecret(providerType: string): boolean {
  return ["openai", "openai_compatible", "relay", "custom"].includes(providerType);
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

function ErrorPanel({ message, compact = false }: { message: string; compact?: boolean }) {
  if (!message) return null;
  return (
    <div className={compact ? "error-panel compact" : "error-panel"} role="alert">
      {message}
    </div>
  );
}

function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      {detail ? <p>{detail}</p> : null}
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
