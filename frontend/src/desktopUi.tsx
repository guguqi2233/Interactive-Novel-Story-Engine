import { ReactNode } from "react";

type StudioHomeProps = {
  [key: string]: any;
};

type LifecycleStatus = "ready" | "warning" | "missing";

type LifecycleChecklistItem = {
  id: string;
  label: string;
  status: LifecycleStatus;
  safeSummary: string;
  nextAction: string;
  jumpTarget: string;
  jumpLabel: string;
};

type AcceptanceChecklistItem = {
  id: string;
  category: string;
  status: LifecycleStatus;
  safeSummary: string;
  nextAction: string;
  jumpTarget: string;
};

function DesktopPlayableHome({
  selectedProjectId,
  currentWorkspaceId,
  selectedWorldId,
  configSummary,
  localConfigSummary,
  safeApiCacheStatuses = [],
  recentProjects = [],
  workspaceTemplates = [],
  saves = [],
  worldHealth,
  status,
  onNavigate,
  onSelectWorkspace,
  onOpenDemoProject
}: {
  selectedProjectId?: string;
  currentWorkspaceId?: string;
  selectedWorldId?: string;
  configSummary?: any;
  localConfigSummary?: any;
  safeApiCacheStatuses?: any[];
  recentProjects?: any[];
  workspaceTemplates?: any[];
  saves?: any[];
  worldHealth?: any;
  status?: any;
  onNavigate?: (mode: string, toolId?: string) => void;
  onSelectWorkspace?: (workspaceId: string) => void;
  onOpenDemoProject?: () => void;
}) {
  const projectId = selectedProjectId || currentWorkspaceId || "";
  const hasProject = Boolean(projectId);
  const providerName = configSummary?.llm_provider ?? localConfigSummary?.provider_type ?? "mock/local_stub";
  const providerConfigured = Boolean(
    configSummary?.api_key_configured ||
    configSummary?.provider_status === "configured" ||
    ["mock", "local_stub"].includes(String(providerName))
  );
  const modelAssignmentChecked = safeApiCacheStatuses.some((cacheStatus) =>
    String(cacheStatus?.key ?? "").includes("provider-model-list") ||
    String(cacheStatus?.key ?? "").includes("model-assignment") ||
    String(cacheStatus?.label ?? "").toLowerCase().includes("model assignment") ||
    String(cacheStatus?.summary ?? "").toLowerCase().includes("model assignment")
  );
  const nextStep = !hasProject
    ? "先打开/创建项目，或体验 Demo 项目。"
    : !providerConfigured
      ? "配置模型服务，然后手动测试连接并读取模型列表。"
      : !modelAssignmentChecked
        ? "为 Novel、Tavern、World、Cross-Mode 和 Quality 分配模型。"
        : "可以继续大世界、写小说或开始角色 RP。";
  const recentSaveCount = saves.length;
  const worldsCount = status?.worlds_count ?? 0;

  return (
    <section className="cn-playable-home" data-testid="v37-cn-playable-home" aria-labelledby="desktop-playable-home-title">
      <div className="cn-playable-hero">
        <div>
          <p className="eyebrow">中文本地可游玩完整产品版</p>
          <h2 id="desktop-playable-home-title">本地 AI 叙事工作室</h2>
          <p className="muted">
            默认面向玩家和创作者：打开本地项目后即可写小说、Tavern RP、玩大世界；Debug、QA、Authoring 和 Diagnostics 收纳在高级工具。
          </p>
        </div>
        <div className="cn-safety-pills" aria-label="本地优先安全摘要">
          <span>无需账号</span>
          <span>不使用云同步</span>
          <span>无在线市场</span>
          <span>不上传项目</span>
        </div>
      </div>

      <div className="cn-primary-actions" aria-label="核心入口">
        <button type="button" onClick={() => onNavigate?.("project")} data-testid="cn-open-project">打开项目</button>
        <button type="button" onClick={() => onNavigate?.("project")} data-testid="cn-create-project">创建项目</button>
        <button type="button" onClick={() => onNavigate?.("prompt_lab")} data-testid="cn-configure-provider">配置模型服务</button>
        <button type="button" onClick={() => onNavigate?.("project")} data-testid="cn-open-novel">写小说</button>
        <button type="button" onClick={() => onNavigate?.("project")} data-testid="cn-open-tavern">角色 RP</button>
        <button type="button" onClick={() => onNavigate?.("play")} data-testid="cn-open-world">大世界游玩</button>
        {hasProject ? (
          <button type="button" onClick={() => onNavigate?.("play")} data-testid="cn-continue-world">
            {recentSaveCount ? "继续大世界" : "开始大世界"}
          </button>
        ) : null}
      </div>

      <div className="cn-project-entry-panel" data-testid="v37-project-entry-panel" aria-label="本地项目入口">
        <div className="cn-project-entry-header">
          <div>
            <h3>{hasProject ? "当前项目" : "先选择本地项目"}</h3>
            <p className="muted">
              {hasProject
                ? `项目已打开：${redactLifecycleText(projectId)}。世界：${redactLifecycleText(selectedWorldId || "未选择")}`
                : "未选择项目时，只需要先打开/创建项目、配置模型服务，或体验 Demo 项目。"}
            </p>
          </div>
          <span className={`status-pill ${hasProject ? "pass" : "warning"}`}>{hasProject ? "项目已打开" : "等待项目"}</span>
        </div>
        <div className="cn-project-entry-actions">
          <button type="button" onClick={() => onNavigate?.("project")} data-testid="cn-project-open-cta">打开项目</button>
          <button type="button" onClick={() => onNavigate?.("project")} data-testid="cn-project-create-cta">创建项目</button>
          <button type="button" onClick={() => onNavigate?.("prompt_lab")} data-testid="cn-project-provider-cta">配置模型服务</button>
          <button type="button" onClick={() => onOpenDemoProject?.()} data-testid="cn-demo-project-entry">体验 Demo 项目</button>
        </div>
        <section className="cn-demo-project-card" data-testid="v37-demo-project-entry" aria-label="Demo 项目一键体验入口">
          <h4>Demo 项目一键体验</h4>
          <p className="muted">
            路径：examples/demo_local_narrative_project。使用 fake/local_stub provider，不需要真实 API key，不上传、不包含 mature/private。
          </p>
          <div className="button-row">
            <button type="button" onClick={() => onOpenDemoProject?.()} data-testid="cn-open-demo-project">体验 Demo 项目</button>
            <button type="button" onClick={() => onNavigate?.("project")} data-testid="cn-demo-try-novel">试写小说</button>
            <button type="button" onClick={() => onNavigate?.("project")} data-testid="cn-demo-try-tavern">试角色 RP</button>
            <button type="button" onClick={() => onNavigate?.("play")} data-testid="cn-demo-try-world">试大世界游玩</button>
          </div>
          <p className="muted">本入口只添加本地工作区引用，不覆盖用户项目、不写真实 key、不调用真实 provider。</p>
        </section>
        <section className="cn-recent-projects" aria-label="最近项目">
          <div className="section-heading-row">
            <h4>最近项目</h4>
            <span className="muted">只显示 safe path summary，不显示完整敏感路径。</span>
          </div>
          {recentProjects.length ? (
            <ul className="compact-list">
              {recentProjects.slice(0, 4).map((project: any) => (
                <li key={project.workspace_id}>
                  <strong>{redactLifecycleText(project.display_name)}</strong>
                  <span className="muted"> - {redactLifecycleText(project.path_redacted ?? project.safe_path_summary ?? "local project")}</span>
                  <button type="button" onClick={() => onSelectWorkspace?.(project.workspace_id)}>打开</button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">暂无最近项目。打开或创建本地项目后，这里会显示脱敏摘要。</p>
          )}
        </section>
      </div>

      <div className="cn-home-summary-grid">
        <DashboardCard title="模型服务状态" value={providerConfigured ? "已配置 / 可手动测试" : "建议配置模型服务"}>
          <p>当前：{redactLifecycleText(providerName)}。真实连接只在用户手动点击 Test Connection / Fetch Models / Generate 时发生。</p>
        </DashboardCard>
        <DashboardCard title="模型分配" value={modelAssignmentChecked ? "已检查" : "待分配"}>
          <p>为 Novel、Tavern、World、Cross-Mode、Quality 分配模型；世界输入解析应使用 JSON / 结构化输出能力。</p>
        </DashboardCard>
        <DashboardCard title="下一步建议" value={nextStep}>
          <p>首页只显示简短状态；完整 readiness、Quality、Debug、Replay 和 Diagnostics 在高级工具中。</p>
        </DashboardCard>
        <DashboardCard title="本地安全状态" value="边界受保护">
          <p>normal UI 不显示 API key、hidden facts、NPC secrets、debug memory 或 raw state_deltas。</p>
        </DashboardCard>
        <DashboardCard title="大世界状态" value={hasProject ? (recentSaveCount ? "可继续" : "可开始") : "需要项目"}>
          <p>{hasProject ? `World packs: ${worldsCount}; Quality: ${worldHealth ? "已运行" : "未运行"}.` : "创建/打开项目后即可开始大世界游玩。"}</p>
        </DashboardCard>
        <DashboardCard title="本地说明" value="无需账号 / 不使用云同步 / 无在线市场">
          <p>Provider Connection & Model Discovery 是本地配置能力，不是 API 转售服务。</p>
        </DashboardCard>
      </div>

      <p className="local-only-note">
        API Key 只通过环境变量、secret_ref、local_secret_ref 或本次 transient key 由后端读取；不会进入 project、frontend storage、logs、backup、diagnostics 或 export。
      </p>
    </section>
  );
}

export function StudioHome(props: StudioHomeProps) {
  const {
    status,
    selectedProjectId,
    selectedWorldId,
    configSummary,
    localConfigSummary,
    localStudioStatus,
    localStudioConfig,
    localStudioStartupChecks,
    backupPlan,
    backupResult,
    restorePlan,
    backupProgress,
    recoveryIssues = [],
    recoveryPlan,
    localLogs,
    diagnosticsBundlePreview,
    diagnosticsBundleCreateResult,
    diagnosticsProgress,
    workspaces = [],
    workspaceTemplates = [],
    recentProjects = [],
    currentWorkspaceId,
    saves = [],
    narrativeEvalReports = [],
    performanceRecent = [],
    performanceSummary,
    eventCount = 0,
    playtestReports = [],
    playtestBatchReport,
    scenarioRegressionCases = [],
    scenarioRegressionRuns = [],
    worldHealth,
    contentCoverage,
    safeApiCacheStatuses = [],
    workflowCheckReport,
    workflowCheckError,
    localUpdateNotes,
    keyboardShortcutsEnabled = true,
    reducedMotionEnabled = false,
    error,
    workspaceError,
    configError,
    localStudioError,
    backupRestoreError,
    recoveryError,
    localLogsError,
    diagnosticsBundleError,
    narrativeEvalError,
    performanceError,
    playtestError,
    scenarioRegressionError,
    worldHealthError,
    contentCoverageError,
    onRefresh,
    onOpenDemoProject,
    onSelectWorkspace,
    onRemoveRecentProject,
    onClearRecentProjects,
    onRefreshLocalConfig,
    onBackupDryRun,
    onCreateBackup,
    onRestoreDryRun,
    onRestoreApply,
    onRefreshRecovery,
    onRefreshLocalLogs,
    onPreviewDiagnosticsBundle,
    onCreateDiagnosticsBundle,
    onRunNarrativeEval,
    onRefreshPerformance,
    onRefreshWorkflowCheck,
    onRunPlaytest,
    onRunPlaytestBatch,
    onRunScenarioRegression,
    onRunWorldHealth,
    onRunContentCoverage,
    onToggleKeyboardShortcuts,
    onToggleReducedMotion,
    onOpenShortcutHelp,
    onNavigate
  } = props;
  const safeWorkspaces = Array.isArray(workspaces) ? workspaces : [];
  const safeWorkspaceTemplates = Array.isArray(workspaceTemplates) ? workspaceTemplates : [];
  const safeRecentProjects = Array.isArray(recentProjects) ? recentProjects : [];
  const safeSaves = Array.isArray(saves) ? saves : [];
  const safeRecoveryIssues = Array.isArray(recoveryIssues) ? recoveryIssues : [];
  const safeNarrativeEvalReports = Array.isArray(narrativeEvalReports) ? narrativeEvalReports : [];
  const safePerformanceRecent = Array.isArray(performanceRecent) ? performanceRecent : [];
  const safePlaytestReports = Array.isArray(playtestReports) ? playtestReports : [];
  const safeScenarioRegressionCases = Array.isArray(scenarioRegressionCases) ? scenarioRegressionCases : [];
  const safeScenarioRegressionRuns = Array.isArray(scenarioRegressionRuns) ? scenarioRegressionRuns : [];
  const safeSafeApiCacheStatuses = Array.isArray(safeApiCacheStatuses) ? safeApiCacheStatuses : [];
  const safeLocalUpdateNotes = localUpdateNotes
    ? { ...localUpdateNotes, release_notes: Array.isArray(localUpdateNotes.release_notes) ? localUpdateNotes.release_notes : [] }
    : undefined;

  return (
    <section className="studio-section desktop-studio-home" data-route-chunk="desktop-ui">
      <DesktopPlayableHome
        selectedProjectId={selectedProjectId}
        currentWorkspaceId={currentWorkspaceId}
        selectedWorldId={selectedWorldId}
        configSummary={configSummary}
        localConfigSummary={localConfigSummary}
        safeApiCacheStatuses={safeSafeApiCacheStatuses}
        recentProjects={safeRecentProjects}
        workspaceTemplates={safeWorkspaceTemplates}
        saves={safeSaves}
        worldHealth={worldHealth}
        status={status}
        onNavigate={onNavigate}
        onSelectWorkspace={onSelectWorkspace}
        onOpenDemoProject={onOpenDemoProject}
      />
      <details className="home-advanced-tools" data-testid="v37-home-advanced-tools" open={false}>
        <summary>高级工具与完整检查 / Advanced Tools</summary>
        <p className="muted">
          Product Readiness、Quality Gate、Debug / Replay、Authoring / Mods、Backup、Diagnostics 等完整检查仍然可用，但默认收纳，避免首页变成开发者仪表盘。
        </p>
      <div className="authoring-pane-header">
        <div>
          <h3>高级本地工作室检查</h3>
          <p className="muted">
            本地启动器、项目、诊断、质量与恢复 dashboard。摘要已脱敏且只在本地处理。
          </p>
        </div>
        <div className="button-row">
          <button type="button" onClick={() => onRefresh?.()}>刷新本地状态</button>
          <button type="button" onClick={() => onNavigate?.("project")}>打开项目工作区</button>
        </div>
      </div>
      <ErrorPanel message={error || localStudioError || configError} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Backend" value={status?.backend ?? localStudioStatus?.backend ?? "unknown"}>
          <p>{localStudioStartupChecks?.backend?.safe_message ?? "Backend status is shown as a safe summary."}</p>
        </DashboardCard>
        <DashboardCard title="Frontend" value={status?.frontend ?? localStudioStatus?.frontend ?? "local"}>
          <p>Frontend build artifacts and node_modules are not included in backups or diagnostics by default.</p>
        </DashboardCard>
        <DashboardCard title="Project" value={selectedProjectId || currentWorkspaceId || "none"}>
          <p>Selected world: {selectedWorldId || "none"}. Recent projects use safe path summaries.</p>
        </DashboardCard>
        <DashboardCard title="Provider" value={configSummary?.llm_provider ?? localConfigSummary?.provider_type ?? "unknown"}>
          <p>{configSummary?.api_key_configured || localConfigSummary?.api_key_configured ? "Configured on backend; key value not shown." : "No API key value displayed."}</p>
        </DashboardCard>
      </div>

      <WorkflowCheckPanel
        report={workflowCheckReport}
        error={workflowCheckError}
        onRefresh={onRefreshWorkflowCheck}
        onNavigate={onNavigate}
      />

      <ProductAcceptanceChecklistPanel
        report={workflowCheckReport}
        selectedProjectId={selectedProjectId}
        currentWorkspaceId={currentWorkspaceId}
        selectedWorldId={selectedWorldId}
        workspaces={safeWorkspaces}
        configSummary={configSummary}
        localConfigSummary={localConfigSummary}
        localStudioConfig={localStudioConfig}
        backupPlan={backupPlan}
        restorePlan={restorePlan}
        diagnosticsBundlePreview={diagnosticsBundlePreview}
        diagnosticsBundleCreateResult={diagnosticsBundleCreateResult}
        worldHealth={worldHealth}
        playtestReports={safePlaytestReports}
        scenarioRegressionRuns={safeScenarioRegressionRuns}
        contentCoverage={contentCoverage}
        safeApiCacheStatuses={safeSafeApiCacheStatuses}
        localUpdateNotes={safeLocalUpdateNotes}
        onRunReadinessCheck={onRefreshWorkflowCheck}
        onNavigate={onNavigate}
      />

      <LocalProjectLifecycleChecklist
        selectedProjectId={selectedProjectId}
        currentWorkspaceId={currentWorkspaceId}
        selectedWorldId={selectedWorldId}
        workspaces={safeWorkspaces}
        workspaceTemplates={safeWorkspaceTemplates}
        recentProjects={safeRecentProjects}
        localStudioStatus={localStudioStatus}
        localStudioConfig={localStudioConfig}
        localConfigSummary={localConfigSummary}
        configSummary={configSummary}
        backupPlan={backupPlan}
        backupResult={backupResult}
        restorePlan={restorePlan}
        diagnosticsBundlePreview={diagnosticsBundlePreview}
        diagnosticsBundleCreateResult={diagnosticsBundleCreateResult}
        worldHealth={worldHealth}
        narrativeEvalReports={safeNarrativeEvalReports}
        contentCoverage={contentCoverage}
        onNavigate={onNavigate}
      />

      <div className="studio-grid two-column-grid">
        <SectionCard title="Project Picker / Recent Projects" description="Local project summaries only; no raw env, database, logs, or hidden GameState.">
          <ErrorPanel message={workspaceError} compact />
          <ItemList
            emptyText="No workspaces loaded."
            items={safeWorkspaces.slice(0, 8).map((workspace: any) => (
              <span key={workspace.workspace_id}>
                {workspace.name} ({workspace.path_redacted}) - {workspace.safe_status}
                <button type="button" onClick={() => onSelectWorkspace?.(workspace.workspace_id)}>Open</button>
              </span>
            ))}
          />
          <ItemList
            emptyText="No recent projects."
            items={safeRecentProjects.slice(0, 6).map((project: any) => (
              <span key={project.workspace_id}>
                {project.display_name} ({project.path_redacted}) - {project.safe_status}
                <button type="button" onClick={() => onRemoveRecentProject?.(project.workspace_id)}>Remove</button>
              </span>
            ))}
          />
          <div className="button-row">
            <button type="button" onClick={() => onClearRecentProjects?.()} disabled={!safeRecentProjects.length}>Clear recent projects</button>
            <button type="button" onClick={() => onNavigate?.("project")}>Project Home</button>
          </div>
          <p className="muted">{safeWorkspaceTemplates.length} local templates available.</p>
        </SectionCard>

        <SectionCard title="Local Settings / Privacy" description="Safe config summary and accessibility preferences.">
          <div className="button-row">
            <button type="button" onClick={() => onRefreshLocalConfig?.()}>Refresh config</button>
            <button type="button" onClick={() => onOpenShortcutHelp?.()}>Shortcut help</button>
          </div>
          <ItemList
            emptyText="No local config summary."
            items={[
              `Debug API: ${localConfigSummary?.debug_api_enabled ? "enabled" : "disabled"}`,
              `Authoring API: ${localConfigSummary?.authoring_api_enabled ? "enabled" : "disabled"}`,
              `Usage tracking: ${localConfigSummary?.usage_tracking_enabled ? "enabled" : "disabled"}`,
              `Keyboard shortcuts: ${keyboardShortcutsEnabled ? "enabled" : "disabled"}`,
              `Reduced motion: ${reducedMotionEnabled ? "enabled" : "disabled"}`
            ].map((item) => <span>{item}</span>)}
          />
          <label>
            <input type="checkbox" checked={keyboardShortcutsEnabled} onChange={(event) => onToggleKeyboardShortcuts?.(event.target.checked)} />
            Keyboard shortcuts enabled
          </label>
          <label>
            <input type="checkbox" checked={reducedMotionEnabled} onChange={(event) => onToggleReducedMotion?.(event.target.checked)} />
            Reduced motion enabled
          </label>
          <p className="muted">Dangerous actions still require explicit confirm and are not bound to direct shortcuts.</p>
        </SectionCard>
      </div>

      <div className="studio-grid two-column-grid">
        <SectionCard title="备份 / 恢复" description="先 dry-run；写入必须显式确认；默认排除敏感内容。">
          <ErrorPanel message={backupRestoreError} compact />
          <ProgressSummary progress={backupProgress} />
          <div className="button-row">
            <button type="button" onClick={() => onBackupDryRun?.()}>备份 dry-run</button>
            <button type="button" onClick={() => onCreateBackup?.()} disabled={!backupPlan}>创建本地备份</button>
            <button type="button" onClick={() => onRestoreDryRun?.()}>恢复 dry-run</button>
            <button type="button" onClick={() => onRestoreApply?.()} disabled={!restorePlan}>确认恢复</button>
          </div>
          <ItemList
            emptyText="尚无备份或恢复结果。"
            items={[
              backupPlan ? `备份计划：包含 ${(backupPlan.included_files ?? []).length} 项，排除 ${(backupPlan.excluded_files ?? []).length} 项` : "",
              backupResult ? `本地备份已创建：${backupResult.backup_id ?? "local"}` : "",
              restorePlan ? `恢复计划：${(restorePlan.conflicts ?? []).length} 个冲突` : ""
            ].filter(Boolean).map((item) => <span>{item}</span>)}
          />
          <p className="muted">默认不包含 API key、.env、provider secrets、debug raw data、mature/private、db/log/cache/build outputs；不会上传。</p>
        </SectionCard>

        <SectionCard title="诊断 / 日志" description="先预览，仅本地，默认脱敏；不会上传。">
          <ErrorPanel message={diagnosticsBundleError || localLogsError} compact />
          <ProgressSummary progress={diagnosticsProgress} />
          <div className="button-row">
            <button type="button" onClick={() => onPreviewDiagnosticsBundle?.()}>预览诊断包</button>
            <button type="button" onClick={() => onCreateDiagnosticsBundle?.()} disabled={!diagnosticsBundlePreview}>创建本地诊断包</button>
            <button type="button" onClick={() => onRefreshLocalLogs?.()}>刷新日志</button>
          </div>
          <ItemList
            emptyText="尚未载入诊断包预览。"
            items={[
              diagnosticsBundlePreview ? `包含内容：${(diagnosticsBundlePreview.included_sections ?? []).length} 项` : "",
              diagnosticsBundlePreview ? `默认排除：${(diagnosticsBundlePreview.excluded_sections ?? []).length} 项` : "",
              diagnosticsBundleCreateResult ? `诊断包：${diagnosticsBundleCreateResult.bundle_id ?? "local"}` : "",
              localLogs ? `近期日志：${(localLogs.entries ?? []).length} 行` : ""
            ].filter(Boolean).map((item) => <span>{item}</span>)}
          />
          <p className="muted">默认不包含 API key、.env、provider secrets、debug raw data、mature/private；诊断包和日志只在本地处理。</p>
        </SectionCard>
      </div>

      <div className="studio-grid two-column-grid">
        <SectionCard title="Quality / Playtest" description="Safe summaries only. No hidden text, raw state_deltas, or provider secrets.">
          <ErrorPanel message={narrativeEvalError || playtestError || scenarioRegressionError || worldHealthError || contentCoverageError} compact />
          <div className="button-row">
            <button type="button" onClick={() => onRunNarrativeEval?.()}>Run quality</button>
            <button type="button" onClick={() => onRunPlaytest?.()}>Run playtest</button>
            <button type="button" onClick={() => onRunPlaytestBatch?.()}>Run batch</button>
            <button type="button" onClick={() => onRunScenarioRegression?.()}>Run regression</button>
            <button type="button" onClick={() => onRunWorldHealth?.()}>World health</button>
            <button type="button" onClick={() => onRunContentCoverage?.()}>Coverage</button>
          </div>
          <div className="studio-grid compact-dashboard-grid">
            <DashboardCard title="Quality Reports" value={String(safeNarrativeEvalReports.length)} />
            <DashboardCard title="Playtests" value={String(safePlaytestReports.length)} />
            <DashboardCard title="Scenario Cases" value={String(safeScenarioRegressionCases.length)} />
            <DashboardCard title="Scenario Runs" value={String(safeScenarioRegressionRuns.length)} />
            <DashboardCard title="World Health" value={worldHealth?.overall_score !== undefined ? String(worldHealth.overall_score) : "empty"} />
            <DashboardCard title="Coverage" value={contentCoverage?.coverage_percent !== undefined ? `${contentCoverage.coverage_percent}%` : "empty"} />
          </div>
        </SectionCard>

        <SectionCard title="Performance / Safe Cache" description="Local metrics and safe cache summaries; no telemetry upload.">
          <ErrorPanel message={performanceError} compact />
          <div className="button-row">
            <button type="button" onClick={() => onRefreshPerformance?.()}>Refresh performance</button>
          </div>
          <div className="studio-grid compact-dashboard-grid">
            <DashboardCard title="Events" value={String(eventCount)} />
            <DashboardCard title="Saves" value={String(safeSaves.length)} />
            <DashboardCard title="Perf Samples" value={String(safePerformanceRecent.length)} />
            <DashboardCard title="Perf Entries" value={String(performanceSummary?.entries?.length ?? 0)} />
            <DashboardCard title="Batch Duration" value={playtestBatchReport?.duration_ms ? `${playtestBatchReport.duration_ms} ms` : "empty"} />
            <DashboardCard title="Safe Cache" value={String(safeSafeApiCacheStatuses.length)} />
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Recovery" description="Safe recovery options only; no direct GameState mutation.">
        <ErrorPanel message={recoveryError} compact />
        <div className="button-row">
          <button type="button" onClick={() => onRefreshRecovery?.()}>Refresh recovery</button>
        </div>
        <ItemList
          emptyText="No recovery issues."
          items={safeRecoveryIssues.slice(0, 8).map((issue: any) => (
            <span key={issue.issue_id ?? issue.code ?? issue.message}>
              {issue.severity ?? "info"}: {issue.safe_summary ?? issue.message ?? "Recovery issue"}
            </span>
          ))}
        />
        {recoveryPlan ? <p className="muted">Recovery plan available. Apply flows remain backend-confirmed and local-only.</p> : null}
      </SectionCard>

      </details>

      <LocalOnlyNotice>
        Dashboard data is a safe local summary. It does not include API keys, raw GameState,
        raw state_deltas, raw prompts, provider secrets, or hidden narrative facts.
      </LocalOnlyNotice>
    </section>
  );
}

function WorkflowCheckPanel({ report, error, onRefresh, onNavigate }: { report: any; error?: string; onRefresh?: () => void; onNavigate?: (mode: string, toolId?: string) => void }) {
  const items = Array.isArray(report?.items) ? report.items : [];
  return (
    <SectionCard title="End-to-End Local Workflow Checker" description="Read-only checklist for project, Provider, Novel, Tavern, World, Cross-Mode, Quality, Backup, Export, Diagnostics, and privacy boundaries.">
      <ErrorPanel message={error} compact />
      <div className="button-row">
        <button type="button" onClick={() => onRefresh?.()}>Run workflow check</button>
        <button type="button" onClick={() => onNavigate?.("project")}>Open Project Home</button>
      </div>
      {report ? (
        <>
          <div className="studio-grid compact-dashboard-grid">
            <DashboardCard title="Overall" value={String(report.overall_status ?? "not_checked")}>
              <p>Local only: {report.local_only ? "yes" : "unknown"}</p>
            </DashboardCard>
            <DashboardCard title="Ready" value={String(report.ready_count ?? 0)} />
            <DashboardCard title="Warnings" value={String(report.warning_count ?? 0)} />
            <DashboardCard title="Missing" value={String(report.missing_count ?? 0)} />
            <DashboardCard title="Disabled / Not checked" value={String((report.disabled_count ?? 0) + (report.not_checked_count ?? 0))} />
            <DashboardCard title="Privacy" value={report.privacy_boundaries_pass ? "pass" : "review"} />
          </div>
          <div className="product-readiness-list" role="list" aria-label="End-to-end local workflow check items">
            {items.map((item: any) => (
              <article className={`product-readiness-item ${workflowStatusTone(item.status)}`} key={item.id} role="listitem">
                <div>
                  <div className="product-readiness-heading">
                    <h4>{item.label}</h4>
                    <span className={`status-pill ${workflowStatusPill(item.status)}`}>{String(item.status).replace("_", " ")}</span>
                  </div>
                  <p>{redactWorkflowText(item.safe_summary)}</p>
                  <p className="muted">Next action: {redactWorkflowText(item.next_action)}</p>
                </div>
                <button type="button" onClick={() => onNavigate?.(workflowJumpMode(item.jump_target))}>
                  Open {workflowJumpLabel(item.jump_target)}
                </button>
              </article>
            ))}
          </div>
        </>
      ) : (
        <p className="muted">No workflow check report loaded yet. Run the read-only check after selecting a local project.</p>
      )}
      <LocalOnlyNotice>
        Workflow check responses never include API keys, transient keys, Authorization headers, raw provider responses, hidden facts, NPC secrets, debug memory, raw prompts, raw outputs, or raw state_deltas.
      </LocalOnlyNotice>
    </SectionCard>
  );
}

function ProductAcceptanceChecklistPanel({
  report,
  selectedProjectId,
  currentWorkspaceId,
  selectedWorldId,
  workspaces = [],
  configSummary,
  localConfigSummary,
  localStudioConfig,
  backupPlan,
  restorePlan,
  diagnosticsBundlePreview,
  diagnosticsBundleCreateResult,
  worldHealth,
  playtestReports = [],
  scenarioRegressionRuns = [],
  contentCoverage,
  safeApiCacheStatuses = [],
  localUpdateNotes,
  onRunReadinessCheck,
  onNavigate
}: {
  report: any;
  selectedProjectId?: string;
  currentWorkspaceId?: string;
  selectedWorldId?: string;
  workspaces?: any[];
  configSummary?: any;
  localConfigSummary?: any;
  localStudioConfig?: any;
  backupPlan?: any;
  restorePlan?: any;
  diagnosticsBundlePreview?: any;
  diagnosticsBundleCreateResult?: any;
  worldHealth?: any;
  playtestReports?: any[];
  scenarioRegressionRuns?: any[];
  contentCoverage?: any;
  safeApiCacheStatuses?: any[];
  localUpdateNotes?: any;
  onRunReadinessCheck?: () => void;
  onNavigate?: (mode: string, toolId?: string) => void;
}) {
  const items = buildProductAcceptanceChecklistItems({
    report,
    selectedProjectId,
    currentWorkspaceId,
    selectedWorldId,
    workspaces,
    configSummary,
    localConfigSummary,
    localStudioConfig,
    backupPlan,
    restorePlan,
    diagnosticsBundlePreview,
    diagnosticsBundleCreateResult,
    worldHealth,
    playtestReports,
    scenarioRegressionRuns,
    contentCoverage,
    safeApiCacheStatuses,
    localUpdateNotes
  });
  const counts = lifecycleCounts(items.map((item) => ({
    id: item.id,
    label: item.category,
    status: item.status,
    safeSummary: item.safeSummary,
    nextAction: item.nextAction,
    jumpTarget: item.jumpTarget,
    jumpLabel: "Jump to issue"
  })));
  return (
    <SectionCard title="Product Acceptance Checklist UI" description="v3.7 local complete product acceptance checklist. It is read-only, safe-summary only, and never uploads data or calls a real provider.">
      <div className="product-acceptance-checklist" data-v37-product-acceptance-checklist="safe-summary">
        <div className="section-heading-row">
          <div>
            <h4>v3.7 Product Acceptance Checklist</h4>
            <p className="muted">Run readiness check to refresh backend safe workflow status, then jump to any warning or missing category.</p>
          </div>
          <button type="button" onClick={() => onRunReadinessCheck?.()}>Run readiness check</button>
        </div>
        <div className="studio-grid compact-dashboard-grid">
          <DashboardCard title="Ready" value={String(counts.ready)} />
          <DashboardCard title="Warnings" value={String(counts.warning)}>
            <p>Warnings identify setup or preview work, not automatic fixes.</p>
          </DashboardCard>
          <DashboardCard title="Missing" value={String(counts.missing)}>
            <p>Missing items include a next local action and a jump target.</p>
          </DashboardCard>
          <DashboardCard title="Workflow check" value={report ? String(report.overall_status ?? "loaded") : "not loaded"}>
            <p>{report ? `Generated at ${redactWorkflowText(report.generated_at ?? "unknown")}.` : "Run readiness check after selecting a local project."}</p>
          </DashboardCard>
        </div>
        <div className="product-readiness-list" role="list" aria-label="v3.7 product acceptance checklist categories">
          {items.map((item) => (
            <article className={`product-readiness-item ${workflowStatusTone(item.status)}`} key={item.id} role="listitem">
              <div>
                <div className="product-readiness-heading">
                  <h4>{item.category}</h4>
                  <span className={`status-pill ${workflowStatusPill(item.status)}`}>{item.status}</span>
                </div>
                <p>{redactWorkflowText(item.safeSummary)}</p>
                <p className="muted">Next action: {redactWorkflowText(item.nextAction)}</p>
              </div>
              <button type="button" onClick={() => onNavigate?.(workflowJumpMode(item.jumpTarget))}>
                Jump to issue
              </button>
            </article>
          ))}
        </div>
        <LocalOnlyNotice>
          Product acceptance checklist rows are safe summaries only. They never show API keys, transient keys, Authorization headers, raw env, raw provider responses, hidden facts, NPC secrets, debug memory, raw prompts, raw outputs, raw state_deltas, or sensitive local paths.
        </LocalOnlyNotice>
      </div>
    </SectionCard>
  );
}

function buildProductAcceptanceChecklistItems(input: {
  report: any;
  selectedProjectId?: string;
  currentWorkspaceId?: string;
  selectedWorldId?: string;
  workspaces: any[];
  configSummary?: any;
  localConfigSummary?: any;
  localStudioConfig?: any;
  backupPlan?: any;
  restorePlan?: any;
  diagnosticsBundlePreview?: any;
  diagnosticsBundleCreateResult?: any;
  worldHealth?: any;
  playtestReports: any[];
  scenarioRegressionRuns: any[];
  contentCoverage?: any;
  safeApiCacheStatuses: any[];
  localUpdateNotes?: any;
}): AcceptanceChecklistItem[] {
  const projectReady = Boolean(input.selectedProjectId || input.currentWorkspaceId);
  const providerType = input.localConfigSummary?.provider_type ?? input.configSummary?.llm_provider ?? "unknown";
  const providerConfigured = Boolean(
    input.configSummary?.api_key_configured ||
    input.localConfigSummary?.api_key_configured ||
    input.configSummary?.provider_status === "configured" ||
    input.configSummary?.provider_status === "connected" ||
    input.localStudioConfig?.provider_profiles_count > 0 ||
    ["mock", "local_stub"].includes(providerType)
  );
  const modelCacheReady = input.safeApiCacheStatuses.some((cacheStatus) =>
    String(cacheStatus?.key ?? "").includes("provider-model-list") ||
    String(cacheStatus?.summary ?? "").toLowerCase().includes("model assignment")
  );
  const qualityReady = Boolean(input.worldHealth || input.contentCoverage || input.playtestReports.length || input.scenarioRegressionRuns.length);
  const backupDiagnosticsReady = Boolean(input.backupPlan || input.restorePlan || input.diagnosticsBundlePreview || input.diagnosticsBundleCreateResult);
  const privacyReady = Boolean(input.localConfigSummary?.local_only && !(input.localConfigSummary?.issues ?? []).some((issue: any) => issue?.severity === "error"));
  const docsReady = Boolean(input.localUpdateNotes?.release_notes?.length);

  const workflowStatus = (keywords: string[], fallback: LifecycleStatus): LifecycleStatus => {
    const items = Array.isArray(input.report?.items) ? input.report.items : [];
    const match = items.find((item: any) => {
      const haystack = `${item?.id ?? ""} ${item?.label ?? ""} ${item?.jump_target ?? ""}`.toLowerCase();
      return keywords.some((keyword) => haystack.includes(keyword));
    });
    return normalizeAcceptanceStatus(match?.status, fallback);
  };

  const item = (
    id: string,
    category: string,
    status: LifecycleStatus,
    safeSummary: string,
    nextAction: string,
    jumpTarget: string
  ): AcceptanceChecklistItem => ({
    id,
    category,
    status,
    safeSummary,
    nextAction,
    jumpTarget
  });

  return [
    item(
      "project-lifecycle",
      "Project lifecycle",
      workflowStatus(["project", "created/opened"], projectReady ? "ready" : input.workspaces.length ? "warning" : "missing"),
      projectReady ? "Local project or workspace is selected for acceptance review." : "No selected local project/workspace is loaded.",
      projectReady ? "Continue with Provider, workflow, and backup checks." : "Create or open a local project from Project Home.",
      "project"
    ),
    item(
      "provider-setup",
      "Provider setup",
      workflowStatus(["provider", "connection", "model list"], providerConfigured && modelCacheReady ? "ready" : providerConfigured ? "warning" : "missing"),
      providerConfigured ? "Provider safe metadata is configured; key values are not shown." : "Missing provider warning: configure mock/local_stub or api_key_env/secret_ref.",
      modelCacheReady ? "Review model assignment by mode." : "Open Provider setup, run user-triggered readiness check, and sync or manually add models.",
      "provider"
    ),
    item(
      "novel-workflow",
      "Novel workflow",
      workflowStatus(["novel"], projectReady ? "ready" : "missing"),
      projectReady ? "Novel workspace can be opened for manuscripts, chapters, quality, and safe export." : "Novel needs a selected local project.",
      projectReady ? "Open Novel and verify manuscript/export readiness." : "Create or open a project first.",
      "novel"
    ),
    item(
      "tavern-workflow",
      "Tavern workflow",
      workflowStatus(["tavern"], projectReady ? "ready" : "missing"),
      projectReady ? "Tavern workspace can be opened for characters, sessions, boundaries, safety, and export." : "Tavern needs a selected local project.",
      projectReady ? "Open Tavern and verify RP safety/export readiness." : "Create or open a project first.",
      "tavern"
    ),
    item(
      "world-workflow",
      "World workflow",
      workflowStatus(["world"], input.selectedWorldId ? "ready" : projectReady ? "warning" : "missing"),
      input.selectedWorldId ? `Selected local world: ${redactWorkflowText(input.selectedWorldId)}.` : "No local world selection is confirmed.",
      "Open World Studio and verify play, visible_state, save/load, timeline, and provider routing.",
      "world"
    ),
    item(
      "cross-mode-workflow",
      "Cross-Mode workflow",
      workflowStatus(["cross", "proposal"], projectReady ? "ready" : "missing"),
      projectReady ? "Cross-Mode draft/proposal/review/apply surfaces are available for the project." : "Cross-Mode needs a selected local project.",
      "Open Cross-Mode review and confirm validation/apply/audit boundaries.",
      "cross_mode"
    ),
    item(
      "authoring-mod-workflow",
      "Authoring / Mod workflow",
      workflowStatus(["authoring", "mod"], input.localConfigSummary?.authoring_api_enabled || input.configSummary?.authoring_api_enabled ? "ready" : "warning"),
      input.localConfigSummary?.authoring_api_enabled || input.configSummary?.authoring_api_enabled
        ? "Authoring / Mod safe draft, validation, permission, import/export, and Safe Apply surfaces are available."
        : "Authoring API is disabled or not checked; package editing remains gated.",
      "Open Authoring / Mod Studio and verify validation, dry-run, permission, compatibility, and confirm flows.",
      "authoring"
    ),
    item(
      "qa-debug-replay-workflow",
      "QA / Debug / Replay workflow",
      workflowStatus(["quality", "debug", "replay"], qualityReady ? "ready" : "warning"),
      qualityReady ? "Quality/playtest/replay signals are available as safe summaries." : "Quality, Debug, Replay, or Playtest summaries have not been checked.",
      "Run Quality Gate or workflow check; raw debug views still require ENABLE_DEBUG_API.",
      "qa_debug"
    ),
    item(
      "backup-restore-diagnostics-workflow",
      "Backup / Restore / Diagnostics workflow",
      workflowStatus(["backup", "restore", "diagnostics"], backupDiagnosticsReady ? "ready" : projectReady ? "warning" : "missing"),
      backupDiagnosticsReady ? "Backup/restore/diagnostics preview data is loaded." : "Backup, restore, and diagnostics previews are not loaded yet.",
      "Run backup dry-run and diagnostics preview before acceptance.",
      "backup"
    ),
    item(
      "export-workflow",
      "Export workflow",
      workflowStatus(["export"], projectReady || input.diagnosticsBundlePreview ? "ready" : "warning"),
      projectReady ? "Local export surfaces are available with preview and filtering summaries." : "Export needs a selected project or diagnostics preview.",
      "Open export/diagnostics and verify secrets, hidden refs, debug, and mature/private are excluded by default.",
      "diagnostics"
    ),
    item(
      "privacy-secrets",
      "Privacy / Secrets",
      workflowStatus(["privacy", "boundaries"], privacyReady ? "ready" : input.localConfigSummary ? "warning" : "missing"),
      privacyReady ? "Local privacy summary reports no config error and secret values stay hidden." : "Privacy summary is missing or has warnings.",
      "Open Settings / Privacy and keep ProviderProfile limited to api_key_env or secret_ref.",
      "privacy"
    ),
    item(
      "documentation",
      "Documentation",
      docsReady ? "ready" : "warning",
      docsReady ? `${input.localUpdateNotes.release_notes.length} local guide/release note summary row(s) are loaded.` : "Offline guide/release-note summaries are not loaded in this session.",
      "Open local help or docs/PRODUCT_GUIDE.md to verify complete product guidance.",
      "project"
    )
  ];
}

function normalizeAcceptanceStatus(status: unknown, fallback: LifecycleStatus): LifecycleStatus {
  if (status === "ready") return "ready";
  if (status === "missing") return "missing";
  if (status === "warning" || status === "disabled" || status === "not_checked") return "warning";
  return fallback;
}

function LocalProjectLifecycleChecklist({
  selectedProjectId,
  currentWorkspaceId,
  selectedWorldId,
  workspaces = [],
  workspaceTemplates = [],
  recentProjects = [],
  localStudioStatus,
  localStudioConfig,
  localConfigSummary,
  configSummary,
  backupPlan,
  backupResult,
  restorePlan,
  diagnosticsBundlePreview,
  diagnosticsBundleCreateResult,
  worldHealth,
  narrativeEvalReports = [],
  contentCoverage,
  onNavigate
}: {
  selectedProjectId?: string;
  currentWorkspaceId?: string;
  selectedWorldId?: string;
  workspaces?: any[];
  workspaceTemplates?: any[];
  recentProjects?: any[];
  localStudioStatus?: any;
  localStudioConfig?: any;
  localConfigSummary?: any;
  configSummary?: any;
  backupPlan?: any;
  backupResult?: any;
  restorePlan?: any;
  diagnosticsBundlePreview?: any;
  diagnosticsBundleCreateResult?: any;
  worldHealth?: any;
  narrativeEvalReports?: any[];
  contentCoverage?: any;
  onNavigate?: (mode: string, toolId?: string) => void;
}) {
  const items = buildLocalProjectLifecycleItems({
    selectedProjectId,
    currentWorkspaceId,
    selectedWorldId,
    workspaces,
    workspaceTemplates,
    recentProjects,
    localStudioStatus,
    localStudioConfig,
    localConfigSummary,
    configSummary,
    backupPlan,
    backupResult,
    restorePlan,
    diagnosticsBundlePreview,
    diagnosticsBundleCreateResult,
    worldHealth,
    narrativeEvalReports,
    contentCoverage
  });
  const counts = lifecycleCounts(items);
  const projectLoaded = Boolean(selectedProjectId || currentWorkspaceId);
  const safePaths = safePathSummaries(workspaces, recentProjects);
  return (
    <SectionCard title="Local Project Lifecycle Checklist" description="Read-only local checklist for create, open, edit, save, backup, restore, export, diagnostics, and privacy boundaries.">
      <div className="product-readiness-dashboard" data-v37-project-lifecycle-checklist="safe-summary">
        <div className="studio-grid compact-dashboard-grid">
          <DashboardCard title="Project" value={projectLoaded ? "ready" : "no project"}>
            <p>{projectLoaded ? "A local project/workspace is selected." : "No project selected yet; use Project Home or Project Picker to create/open one."}</p>
          </DashboardCard>
          <DashboardCard title="Ready" value={String(counts.ready)} />
          <DashboardCard title="Warnings" value={String(counts.warning)}>
            <p>Warnings are local setup gaps, not release-blocking secrets.</p>
          </DashboardCard>
          <DashboardCard title="Missing" value={String(counts.missing)}>
            <p>Missing items show the next local step without reading arbitrary files.</p>
          </DashboardCard>
        </div>
        <div className="product-readiness-list" role="list" aria-label="Local project lifecycle checklist items">
          {items.map((item) => (
            <article className={`product-readiness-item ${lifecycleStatusTone(item.status)}`} key={item.id} role="listitem">
              <div>
                <div className="product-readiness-heading">
                  <h4>{item.label}</h4>
                  <span className={`status-pill ${lifecycleStatusPill(item.status)}`}>{item.status}</span>
                </div>
                <p>{redactLifecycleText(item.safeSummary)}</p>
                <p className="muted">Next action: {redactLifecycleText(item.nextAction)}</p>
              </div>
              <button type="button" onClick={() => onNavigate?.(lifecycleJumpMode(item.jumpTarget))}>
                {item.jumpLabel}
              </button>
            </article>
          ))}
        </div>
        <div className="lifecycle-safe-path-summary">
          <h4>Safe path summary</h4>
          <p className="muted">Only redacted workspace/recent-project summaries are shown. Raw local paths, .env, databases, logs, caches, and build outputs stay out of normal UI.</p>
          <ItemList
            emptyText="No safe project path summary loaded yet."
            items={safePaths.map((path) => <span key={path}>{path}</span>)}
          />
        </div>
        <LocalOnlyNotice>
          Local project lifecycle checks do not upload data, do not call real providers, and do not read arbitrary files from the UI,
          modify GameState, or display API keys, hidden facts, raw debug data, raw prompts, raw outputs, or raw state_deltas.
        </LocalOnlyNotice>
      </div>
    </SectionCard>
  );
}

function buildLocalProjectLifecycleItems(input: {
  selectedProjectId?: string;
  currentWorkspaceId?: string;
  selectedWorldId?: string;
  workspaces: any[];
  workspaceTemplates: any[];
  recentProjects: any[];
  localStudioStatus?: any;
  localStudioConfig?: any;
  localConfigSummary?: any;
  configSummary?: any;
  backupPlan?: any;
  backupResult?: any;
  restorePlan?: any;
  diagnosticsBundlePreview?: any;
  diagnosticsBundleCreateResult?: any;
  worldHealth?: any;
  narrativeEvalReports: any[];
  contentCoverage?: any;
}): LifecycleChecklistItem[] {
  const projectLoaded = Boolean(input.selectedProjectId || input.currentWorkspaceId);
  const workspaceAvailable = input.workspaces.length > 0;
  const localStudioReady = Boolean(input.localStudioStatus || input.localStudioConfig || input.localConfigSummary);
  const backupReady = Boolean(input.backupPlan || input.backupResult);
  const diagnosticsReady = Boolean(input.diagnosticsBundlePreview || input.diagnosticsBundleCreateResult);
  const qualityReady = Boolean(input.worldHealth || input.narrativeEvalReports.length || input.contentCoverage);
  const providerConfigured = Boolean(input.configSummary?.llm_provider || input.localConfigSummary?.provider_type || input.configSummary?.api_key_configured || input.localConfigSummary?.api_key_configured);
  const safePaths = safePathSummaries(input.workspaces, input.recentProjects);
  return [
    lifecycleItem(
      "create_project",
      "Create project",
      input.workspaceTemplates.length || projectLoaded ? "ready" : "warning",
      input.workspaceTemplates.length
        ? `${input.workspaceTemplates.length} local template(s) are available for creating a project.`
        : projectLoaded
          ? "A local project already exists; create remains available from Project Home."
          : "No project exists yet, but Project Home provides a local create flow.",
      "Open Project Home and create a NarrativeProject or local workspace. This does not modify active GameState.",
      "project",
      "Open Project Home"
    ),
    lifecycleItem(
      "open_project",
      "Open project",
      projectLoaded ? "ready" : workspaceAvailable ? "warning" : "missing",
      projectLoaded
        ? `Selected local project/workspace: ${redactLifecycleText(input.selectedProjectId || input.currentWorkspaceId)}.`
        : workspaceAvailable
          ? `${input.workspaces.length} local workspace summary row(s) are available to open.`
          : "No local workspace/project summary is loaded.",
      "Use Project Picker or Project Home. Recent/open flows use safe summaries only.",
      "project",
      "Open Project Picker"
    ),
    lifecycleItem(
      "recent_projects",
      "Recent projects",
      input.recentProjects.length ? "ready" : "warning",
      input.recentProjects.length
        ? `${input.recentProjects.length} recent project safe summar${input.recentProjects.length === 1 ? "y is" : "ies are"} available.`
        : "No recent projects yet; this is friendly for first-run/no-project state.",
      "Open or create a project; recent entries store redacted safe path summaries only.",
      "project",
      "Open Recent Projects"
    ),
    lifecycleItem(
      "project_health_check",
      "Project health check",
      localStudioReady ? "ready" : "warning",
      localStudioReady ? "Local launcher/status/config summaries are available." : "Project/local studio health has not been refreshed yet.",
      "Refresh local status or run Desktop Health Check. Reports stay local and redacted.",
      "settings",
      "Open Health"
    ),
    lifecycleItem(
      "project_settings",
      "Project settings",
      localStudioReady ? "ready" : "warning",
      localStudioReady ? "Local settings summary is available without raw env values." : "Local settings summary is not loaded.",
      "Open Local Settings / Privacy to refresh config. Raw env and secrets are not rendered.",
      "settings",
      "Open Settings"
    ),
    lifecycleItem(
      "provider_settings",
      "Provider settings",
      providerConfigured ? "ready" : "warning",
      providerConfigured ? "Provider metadata is configured or visible through safe backend summaries." : "Provider setup is not confirmed yet.",
      "Open Provider Connectivity. Configure api_key_env or secret_ref only; do not paste raw keys.",
      "provider",
      "Open Provider"
    ),
    lifecycleItem(
      "quality_gate",
      "Quality Gate",
      qualityReady ? "ready" : "warning",
      qualityReady ? "Quality or health summaries are loaded." : "No Quality Gate or world health report is loaded.",
      "Run local Quality Gate or World Health before export/release review.",
      "quality",
      "Open Quality"
    ),
    lifecycleItem(
      "backup",
      "Backup",
      backupReady ? "ready" : "warning",
      backupReady ? "Backup dry-run/create metadata is available." : "Backup missing warning: run backup dry-run before creating a backup.",
      "Run Backup dry-run first. Create remains disabled until preview exists and blockers are clear.",
      "backup",
      "Open Backup"
    ),
    lifecycleItem(
      "restore_dry_run",
      "Restore dry-run",
      input.restorePlan ? "ready" : "warning",
      input.restorePlan ? "Restore dry-run preview is available; no project files were overwritten." : "Restore dry-run has not been run yet.",
      "Use Restore dry-run before any confirmed restore. Destructive restore requires explicit confirm.",
      "backup",
      "Open Restore"
    ),
    lifecycleItem(
      "diagnostics_preview",
      "Diagnostics preview",
      diagnosticsReady ? "ready" : "warning",
      diagnosticsReady ? "Diagnostics preview/create metadata is available and local-only." : "Diagnostics safe warning: preview has not been loaded yet.",
      "Preview diagnostics before create. The flow is local-only and redacted by default.",
      "diagnostics",
      "Open Diagnostics"
    ),
    lifecycleItem(
      "export",
      "Export",
      projectLoaded || input.selectedWorldId ? "ready" : "warning",
      projectLoaded || input.selectedWorldId ? "Local export surfaces are reachable with safe export defaults." : "Export is waiting for a selected local project or world.",
      "Use Novel/Tavern/Authoring export previews; defaults filter secrets, debug, hidden, and mature/private data.",
      "export",
      "Open Export"
    ),
    lifecycleItem(
      "safe_path_summary",
      "Safe path summary",
      safePaths.length ? "ready" : "warning",
      safePaths.length ? `${safePaths.length} redacted path summar${safePaths.length === 1 ? "y is" : "ies are"} available.` : "No safe path summary is loaded yet.",
      "Use Project Picker/Recent Projects. Do not expose raw local paths unless explicitly needed for a safe file picker.",
      "project",
      "Open Project Picker"
    ),
    lifecycleItem(
      "local_privacy_notice",
      "Local privacy notice",
      "ready",
      "Local-first privacy notice is visible: no upload, no cloud sync, no accounts, no online project service.",
      "Keep lifecycle, backup, diagnostics, export, and cache summaries redacted.",
      "privacy",
      "Open Privacy"
    )
  ];
}

function lifecycleItem(
  id: string,
  label: string,
  status: LifecycleStatus,
  safeSummary: string,
  nextAction: string,
  jumpTarget: string,
  jumpLabel: string
): LifecycleChecklistItem {
  return { id, label, status, safeSummary, nextAction, jumpTarget, jumpLabel };
}

function lifecycleCounts(items: LifecycleChecklistItem[]): { ready: number; warning: number; missing: number } {
  return {
    ready: items.filter((item) => item.status === "ready").length,
    warning: items.filter((item) => item.status === "warning").length,
    missing: items.filter((item) => item.status === "missing").length
  };
}

function lifecycleStatusPill(status: LifecycleStatus): string {
  if (status === "ready") return "pass";
  if (status === "missing") return "error";
  return "warning";
}

function lifecycleStatusTone(status: LifecycleStatus): string {
  if (status === "ready") return "ready";
  if (status === "missing") return "missing";
  return "warning";
}

function lifecycleJumpMode(target: string): string {
  const mapping: Record<string, string> = {
    project: "project",
    settings: "studio",
    provider: "prompt_lab",
    quality: "studio",
    backup: "studio",
    diagnostics: "studio",
    export: "authoring",
    privacy: "studio"
  };
  return mapping[target] ?? "studio";
}

function safePathSummaries(workspaces: any[], recentProjects: any[]): string[] {
  const values = [
    ...workspaces.map((workspace) => workspace?.path_redacted || workspace?.safe_path_summary || workspace?.safe_summary),
    ...recentProjects.map((project) => project?.path_redacted || project?.safe_path_summary || project?.safe_summary)
  ]
    .filter(Boolean)
    .map((value) => redactLifecycleText(value));
  return Array.from(new Set(values)).slice(0, 8);
}

function redactLifecycleText(value: unknown): string {
  return String(value ?? "")
    .replace(/[A-Z]:\\[^\s"'<>]+/g, "[local path redacted]")
    .replace(/\/(?:Users|home|var|tmp)\/[^\s"'<>]+/g, "[local path redacted]")
    .replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]")
    .replace(/Authorization\s*[:=]\s*Bearer\s+\S+/gi, "Authorization: Bearer [redacted]")
    .replace(/transient_api_key/gi, "transient key")
    .replace(/api[_ -]?key\s*[:=]\s*\S+/gi, "api key: [redacted]");
}

function workflowStatusPill(status: string): string {
  if (status === "ready") return "pass";
  if (status === "missing") return "error";
  return "warning";
}

function workflowStatusTone(status: string): string {
  if (status === "ready") return "ready";
  if (status === "missing") return "missing";
  if (status === "disabled") return "disabled";
  if (status === "not_checked") return "not-checked";
  return "warning";
}

function workflowJumpMode(target: string): string {
  const mapping: Record<string, string> = {
    project: "project",
    provider: "prompt_lab",
    novel: "project",
    tavern: "project",
    world: "play",
    cross_mode: "project",
    authoring: "authoring",
    quality: "studio",
    qa_debug: "studio",
    backup: "studio",
    diagnostics: "studio",
    privacy: "studio"
  };
  return mapping[target] ?? "studio";
}

function workflowJumpLabel(target: string): string {
  const mapping: Record<string, string> = {
    project: "Project",
    provider: "Provider",
    novel: "Novel",
    tavern: "Tavern",
    world: "World",
    cross_mode: "Cross-Mode",
    authoring: "Authoring",
    quality: "Quality",
    qa_debug: "QA / Debug",
    backup: "Backup",
    diagnostics: "Diagnostics",
    privacy: "Privacy"
  };
  return mapping[target] ?? "Dashboard";
}

function redactWorkflowText(value: unknown): string {
  return String(value ?? "")
    .replace(/[A-Z]:\\[^\s"'<>]+/g, "[local path redacted]")
    .replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]")
    .replace(/Authorization\s*[:=]\s*Bearer\s+\S+/gi, "Authorization: Bearer [redacted]")
    .replace(/transient_api_key/gi, "transient key");
}

function ProgressSummary({ progress }: { progress: any }) {
  if (!progress) return <p className="muted">No long-running operation in progress.</p>;
  const stage = progress.stage ?? progress.current_stage ?? "running";
  const percent = progress.percent ?? progress.progress_percent;
  return (
    <div className="progress-summary" aria-live="polite">
      <strong>{stage}</strong>
      <p className="muted">{percent !== undefined ? `${percent}% complete` : "Working locally."}</p>
      <p className="muted">Excluded by default: .env, API keys, provider secrets, debug, mature/private, db/log/cache/build outputs.</p>
    </div>
  );
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

function ErrorPanel({ message, compact = false }: { message?: string; compact?: boolean }) {
  if (!message) return null;
  const safeMessage = String(message).replace(/[A-Z]:\\[^\s"'<>]+/g, "[local path redacted]").replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]");
  return (
    <div className={compact ? "error-panel compact" : "error-panel"} role="alert">
      <strong>请求失败</strong>
      <p>{safeMessage}</p>
      <p className="muted">建议：重试本地操作，检查后端健康状态，或打开诊断查看脱敏预览。</p>
      <span className="sr-only">Suggested fix: retry the local action, check backend health, or open Diagnostics for a redacted preview.</span>
    </div>
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

function LocalOnlyNotice({ children }: { children: ReactNode }) {
  return <p className="local-only-note">{children}</p>;
}
