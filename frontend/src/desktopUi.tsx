import { ReactNode } from "react";

type StudioHomeProps = {
  [key: string]: any;
};

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

  return (
    <section className="studio-section desktop-studio-home" data-route-chunk="desktop-ui">
      <div className="authoring-pane-header">
        <div>
          <h3>Local Desktop Studio</h3>
          <p className="muted">
            Lazy-loaded local launcher, project, diagnostics, quality, and recovery dashboard. Summaries are redacted and local-only.
          </p>
        </div>
        <div className="button-row">
          <button type="button" onClick={() => onRefresh?.()}>Refresh local status</button>
          <button type="button" onClick={() => onNavigate?.("project")}>Open Project Workspace</button>
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

      <div className="studio-grid two-column-grid">
        <SectionCard title="Project Picker / Recent Projects" description="Local project summaries only; no raw env, database, logs, or hidden GameState.">
          <ErrorPanel message={workspaceError} compact />
          <ItemList
            emptyText="No workspaces loaded."
            items={workspaces.slice(0, 8).map((workspace: any) => (
              <span key={workspace.workspace_id}>
                {workspace.name} ({workspace.path_redacted}) - {workspace.safe_status}
                <button type="button" onClick={() => onSelectWorkspace?.(workspace.workspace_id)}>Open</button>
              </span>
            ))}
          />
          <ItemList
            emptyText="No recent projects."
            items={recentProjects.slice(0, 6).map((project: any) => (
              <span key={project.workspace_id}>
                {project.display_name} ({project.path_redacted}) - {project.safe_status}
                <button type="button" onClick={() => onRemoveRecentProject?.(project.workspace_id)}>Remove</button>
              </span>
            ))}
          />
          <div className="button-row">
            <button type="button" onClick={() => onClearRecentProjects?.()} disabled={!recentProjects.length}>Clear recent projects</button>
            <button type="button" onClick={() => onNavigate?.("project")}>Project Home</button>
          </div>
          <p className="muted">{workspaceTemplates.length} local templates available.</p>
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
        <SectionCard title="Backup / Restore" description="Dry-run first, explicit confirm for writes, default exclusions stay active.">
          <ErrorPanel message={backupRestoreError} compact />
          <ProgressSummary progress={backupProgress} />
          <div className="button-row">
            <button type="button" onClick={() => onBackupDryRun?.()}>Backup dry-run</button>
            <button type="button" onClick={() => onCreateBackup?.()} disabled={!backupPlan}>Create backup</button>
            <button type="button" onClick={() => onRestoreDryRun?.()}>Restore dry-run</button>
            <button type="button" onClick={() => onRestoreApply?.()} disabled={!restorePlan}>Apply restore</button>
          </div>
          <ItemList
            emptyText="No backup or restore result yet."
            items={[
              backupPlan ? `Backup plan: ${(backupPlan.included_files ?? []).length} included, ${(backupPlan.excluded_files ?? []).length} excluded` : "",
              backupResult ? `Backup created: ${backupResult.backup_id ?? "local"}` : "",
              restorePlan ? `Restore plan: ${(restorePlan.conflicts ?? []).length} conflicts` : ""
            ].filter(Boolean).map((item) => <span>{item}</span>)}
          />
        </SectionCard>

        <SectionCard title="Diagnostics / Logs" description="Preview-first, local-only, redacted by default.">
          <ErrorPanel message={diagnosticsBundleError || localLogsError} compact />
          <ProgressSummary progress={diagnosticsProgress} />
          <div className="button-row">
            <button type="button" onClick={() => onPreviewDiagnosticsBundle?.()}>Preview diagnostics</button>
            <button type="button" onClick={() => onCreateDiagnosticsBundle?.()} disabled={!diagnosticsBundlePreview}>Create diagnostics</button>
            <button type="button" onClick={() => onRefreshLocalLogs?.()}>Refresh logs</button>
          </div>
          <ItemList
            emptyText="No diagnostics preview loaded."
            items={[
              diagnosticsBundlePreview ? `Included sections: ${(diagnosticsBundlePreview.included_sections ?? []).length}` : "",
              diagnosticsBundlePreview ? `Excluded sections: ${(diagnosticsBundlePreview.excluded_sections ?? []).length}` : "",
              diagnosticsBundleCreateResult ? `Bundle: ${diagnosticsBundleCreateResult.bundle_id ?? "local"}` : "",
              localLogs ? `Recent log rows: ${(localLogs.entries ?? []).length}` : ""
            ].filter(Boolean).map((item) => <span>{item}</span>)}
          />
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
            <DashboardCard title="Quality Reports" value={String(narrativeEvalReports.length)} />
            <DashboardCard title="Playtests" value={String(playtestReports.length)} />
            <DashboardCard title="Scenario Cases" value={String(scenarioRegressionCases.length)} />
            <DashboardCard title="Scenario Runs" value={String(scenarioRegressionRuns.length)} />
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
            <DashboardCard title="Saves" value={String(saves.length)} />
            <DashboardCard title="Perf Samples" value={String(performanceRecent.length)} />
            <DashboardCard title="Perf Entries" value={String(performanceSummary?.entries?.length ?? 0)} />
            <DashboardCard title="Batch Duration" value={playtestBatchReport?.duration_ms ? `${playtestBatchReport.duration_ms} ms` : "empty"} />
            <DashboardCard title="Safe Cache" value={String(safeApiCacheStatuses.length)} />
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
          items={recoveryIssues.slice(0, 8).map((issue: any) => (
            <span key={issue.issue_id ?? issue.code ?? issue.message}>
              {issue.severity ?? "info"}: {issue.safe_summary ?? issue.message ?? "Recovery issue"}
            </span>
          ))}
        />
        {recoveryPlan ? <p className="muted">Recovery plan available. Apply flows remain backend-confirmed and local-only.</p> : null}
      </SectionCard>

      <LocalOnlyNotice>
        Dashboard data is a safe local summary. It does not include API keys, raw GameState,
        raw state_deltas, raw prompts, provider secrets, or hidden narrative facts.
      </LocalOnlyNotice>
    </section>
  );
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
  return (
    <div className={compact ? "error-panel compact" : "error-panel"} role="alert">
      {String(message).replace(/[A-Z]:\\[^\s"'<>]+/g, "[local path redacted]").replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]")}
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
