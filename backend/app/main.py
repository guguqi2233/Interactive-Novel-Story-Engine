import json
import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.api import (
    AuthoringCreateWorldRequest,
    AuthoringCreateWorldResponse,
    AuthoringFileListResponse,
    AuthoringFilePreviewResponse,
    AuthoringFileResponse,
    AuthoringDraftFileRequest,
    AuthoringFileWriteRequest,
    AuthoringFileWriteResponse,
    AuthoringModListResponse,
    AuthoringModDetailResponse,
    AuthoringModLoadOrderResponse,
    AuthoringModSummaryResponse,
    AuthoringModValidationResponse,
    ArchiveExportResponse,
    ArchiveImportRequest,
    ArchiveImportResponse,
    ScenarioTemplateListResponse,
    ScenarioTemplateOutputFileResponse,
    ScenarioTemplatePreviewResponse,
    ScenarioTemplateRenderRequest,
    ScenarioTemplateResponse,
    RenderedScenarioTemplateFileResponse,
    RenderedScenarioTemplateResponse,
    AuthoringDiffSummaryResponse,
    AuthoringImpactAnalysisResponse,
    AuthoringValidationIssueResponse,
    AuthoringValidationResponse,
    AuthoringWorldDetailResponse,
    AuthoringWorldListResponse,
    AuthoringWorldSummaryResponse,
    DeleteSaveResponse,
    GameInputRequest,
    GameInputResponse,
    GameStateResponse,
    DebugEventListResponse,
    DebugEventResponse,
    DebugPerformanceRecentResponse,
    DebugPerformanceSampleResponse,
    DebugPerformanceSummaryEntryResponse,
    DebugPerformanceSummaryResponse,
    LoadGameResponse,
    MigrationHistoryEntryResponse,
    MigrationInfoResponse,
    MigrationListResponse,
    NarrativeEvalCaseResultResponse,
    NarrativeEvalRecentResponse,
    NarrativeEvalReportResponse,
    PlaytestRecentResponse,
    PlaytestReportResponse,
    PlaytestRunRequest,
    QuestGraphPreviewRequest,
    QuestGraphPreviewResponse,
    QuestGraphResponse,
    SaveGameResponse,
    SaveListResponse,
    SaveMigrationResponse,
    SaveMigrationStatusResponse,
    SaveSummaryResponse,
    StartGameRequest,
    StartGameResponse,
    StudioConfigSummaryResponse,
    StudioPlaytestSummaryResponse,
    StudioStatusResponse,
    StudioValidationSummaryResponse,
)
from app.config import get_settings
from app.core.event_log import Event
from app.core.instrumentation import (
    get_performance_recorder,
    performance_logging_enabled,
    set_performance_logging_enabled,
)
from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.core.world_state import GameState
from app.db.migrations import CURRENT_ENGINE_VERSION
from app.db.models import SaveGame
from app.db.migration_service import MigrationService
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository
from app.db.save_service import SaveService
from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.import_export import ImportExportError, ImportExportService
from app.engine.content.mod_loader import ModInfo, ModLoader, ModLoaderError, ModValidationReport
from app.engine.content.scenario_templates import (
    RenderedTemplate,
    ScenarioTemplate,
    ScenarioTemplateError,
    ScenarioTemplatePreview,
    ScenarioTemplateRenderer,
)
from app.engine.content.quest_graph import (
    QuestGraph,
    QuestGraphError,
    parse_quest_graph,
    preview_quest_graph,
)
from app.engine.content.validator import ValidationReport
from app.engine.content.world_loader import WorldLoaderError
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.time import format_game_time
from app.evals.narrative_quality import (
    NarrativeQualityReport,
    run_narrative_quality_evals,
    sample_narrative_quality_cases,
)
from app.engine.rules.graphs import (
    FactionGraph,
    RelationshipGraph,
    build_faction_graph,
    build_relationship_graph,
)
from app.llm.provider_base import LLMProviderError
from app.playtesting.runner import PlaytestOptions, PlaytestReport, run_playtest
from app.session_store import InMemorySessionStore, build_visible_state


def _sqlite_path_from_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    if database_url.startswith("sqlite://"):
        return database_url.removeprefix("sqlite://")
    return database_url


settings = get_settings()
set_performance_logging_enabled(settings.enable_perf_logging)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.session_store = InMemorySessionStore()
app.state.save_repository = SQLiteSaveRepository(_sqlite_path_from_url(settings.database_url))
app.state.narrative_eval_reports = []
app.state.playtest_reports = []
app.state.scenario_template_renderer = ScenarioTemplateRenderer()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/studio/status", response_model=StudioStatusResponse)
def get_studio_status() -> StudioStatusResponse:
    sync_runtime_settings()
    active_settings = getattr(app.state, "settings", settings)
    authoring_service = get_authoring_service()
    worlds = authoring_service.list_worlds()
    recent_saves: list[SaveSummaryResponse] = []
    try:
        recent_saves = [_save_summary_response(save) for save in get_save_repository().list_saves()[:5]]
    except SaveRepositoryError:
        recent_saves = []

    validation_summaries: list[StudioValidationSummaryResponse] = []
    for world in worlds:
        try:
            report = authoring_service.validate_world(world.world_id)
            validation_summaries.append(
                StudioValidationSummaryResponse(
                    world_id=world.world_id,
                    ok=report.ok,
                    error_count=len(report.errors),
                    warning_count=len(report.warnings),
                )
            )
        except Exception:
            validation_summaries.append(
                StudioValidationSummaryResponse(
                    world_id=world.world_id,
                    ok=False,
                    error_count=1,
                    warning_count=0,
                )
            )

    playtest_reports = get_playtest_reports()
    latest_playtest = playtest_reports[-1] if playtest_reports else None

    return StudioStatusResponse(
        engine_version=CURRENT_ENGINE_VERSION,
        schema_version=CURRENT_GAME_STATE_SCHEMA_VERSION,
        backend_status="ok",
        worlds_count=len(worlds),
        recent_saves=recent_saves,
        authoring_api_enabled=bool(active_settings.enable_authoring_api),
        debug_api_enabled=bool(active_settings.enable_debug_api),
        performance_logging_enabled=performance_logging_enabled(),
        llm_provider=active_settings.llm_provider,
        local_model_provider_status=_local_model_provider_status(active_settings),
        validation_summaries=validation_summaries,
        playtest_summary=StudioPlaytestSummaryResponse(
            available=playtest_api_enabled(),
            recent_runs=len(playtest_reports),
            latest_status=_playtest_status_label(latest_playtest) if latest_playtest else None,
        ),
    )


def _local_model_provider_status(active_settings: object) -> str | None:
    provider = str(getattr(active_settings, "llm_provider", "mock")).lower()
    if provider == "local_stub":
        return "local_stub ready"
    if provider == "local_http":
        base_url = getattr(active_settings, "local_llm_base_url", None)
        if not base_url:
            return "missing LOCAL_LLM_BASE_URL"
        json_mode = "json_mode=on" if getattr(active_settings, "local_llm_json_mode", True) else "json_mode=off"
        return f"configured ({json_mode})"
    return None


def _playtest_status_label(report: PlaytestReportResponse | None) -> str | None:
    if report is None:
        return None
    if report.errors or report.invariant_violations or report.visibility_leaks or report.save_load_failures:
        return "issues found"
    return "passed"


@app.get("/studio/config-summary", response_model=StudioConfigSummaryResponse)
def get_studio_config_summary() -> StudioConfigSummaryResponse:
    sync_runtime_settings()
    active_settings = getattr(app.state, "settings", settings)
    provider = str(active_settings.llm_provider).strip().lower()
    return StudioConfigSummaryResponse(
        llm_provider=provider,
        provider_status=_provider_status_label(active_settings),
        provider_sends_prompts_off_machine=provider in {"openai", "local_http"},
        authoring_api_enabled=bool(active_settings.enable_authoring_api),
        debug_api_enabled=bool(active_settings.enable_debug_api),
        performance_logging_enabled=performance_logging_enabled(),
        playtest_api_enabled=playtest_api_enabled(),
        eval_api_enabled=bool(getattr(active_settings, "enable_eval_api", False) or active_settings.enable_debug_api),
        database_configured=bool(active_settings.database_url),
        database_path_hint=_redacted_database_hint(active_settings.database_url),
        api_key_configured=bool(active_settings.llm_api_key),
        privacy_notes=[
            "GameState, saves, memory records, and content packs are stored locally.",
            "Only the configured LLM provider may receive prompts; API keys are never returned by this endpoint.",
            "Authoring, debug, performance, playtest, and eval APIs are local studio tools.",
            "Mods are validated as local YAML/content packages and are not executed as code.",
        ],
    )


def _provider_status_label(active_settings: object) -> str:
    provider = str(getattr(active_settings, "llm_provider", "mock")).strip().lower()
    if provider == "mock":
        return "mock provider; no external LLM calls"
    if provider == "local_stub":
        return "local stub provider; no network calls"
    if provider == "local_http":
        if not getattr(active_settings, "local_llm_base_url", None):
            return "local_http missing LOCAL_LLM_BASE_URL"
        return "local_http configured; prompts are sent to the configured local endpoint"
    if provider == "openai":
        if not getattr(active_settings, "llm_api_key", None):
            return "openai selected but LLM_API_KEY is not configured"
        return "openai configured; prompts may be sent to the provider API"
    return f"unsupported provider: {provider}"


def _redacted_database_hint(database_url: str) -> str:
    if not database_url:
        return "not configured"
    if database_url.startswith("sqlite:///") or database_url.startswith("sqlite://"):
        path = Path(_sqlite_path_from_url(database_url))
        return f"sqlite local file: {path.name or '[configured]'}"
    return "database URL configured (redacted)"


def get_session_store() -> InMemorySessionStore:
    return app.state.session_store


def get_save_repository() -> SQLiteSaveRepository:
    return app.state.save_repository


def get_migration_service() -> MigrationService:
    return MigrationService(get_save_repository())


def debug_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_debug_api)


def sync_runtime_settings() -> None:
    active_settings = getattr(app.state, "settings", settings)
    set_performance_logging_enabled(bool(active_settings.enable_perf_logging))


def authoring_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_authoring_api)


def require_debug_api() -> None:
    sync_runtime_settings()
    if not debug_api_enabled():
        raise HTTPException(status_code=403, detail="Debug API is disabled")


def playtest_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(getattr(active_settings, "enable_playtest_api", False) or active_settings.enable_debug_api)


def require_playtest_api() -> None:
    sync_runtime_settings()
    if not playtest_api_enabled():
        raise HTTPException(status_code=403, detail="Playtest API is disabled")


def get_narrative_eval_reports() -> list[NarrativeQualityReport]:
    reports = getattr(app.state, "narrative_eval_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.narrative_eval_reports = reports
    return reports


def get_playtest_reports() -> list[PlaytestReportResponse]:
    reports = getattr(app.state, "playtest_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.playtest_reports = reports
    return reports


def require_authoring_api() -> None:
    if not authoring_api_enabled():
        raise HTTPException(status_code=403, detail="Authoring API is disabled")


def get_worlds_root() -> str:
    return str(getattr(app.state, "worlds_root", "worlds"))


def get_mods_root() -> str:
    return str(getattr(app.state, "mods_root", "mods"))


def get_authoring_service() -> ContentAuthoringService:
    return ContentAuthoringService(get_worlds_root())


def get_scenario_template_renderer() -> ScenarioTemplateRenderer:
    renderer = getattr(app.state, "scenario_template_renderer", None)
    if isinstance(renderer, ScenarioTemplateRenderer):
        return renderer
    renderer = ScenarioTemplateRenderer(worlds_root=get_worlds_root())
    app.state.scenario_template_renderer = renderer
    return renderer


def get_mod_loader() -> ModLoader:
    return ModLoader(get_mods_root())


def get_import_export_service() -> ImportExportService:
    return ImportExportService(
        worlds_root=get_worlds_root(),
        mods_root=get_mods_root(),
        repository=get_save_repository(),
    )


@app.post("/game/start", response_model=StartGameResponse)
def start_game(request: StartGameRequest | None = None) -> StartGameResponse:
    world_id = request.world_id if request else None
    try:
        session_id, game_loop = get_session_store().create_session(world_id)
    except WorldLoaderError as exc:
        status_code = 404 if str(exc).startswith("World pack not found:") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return StartGameResponse(
        session_id=session_id,
        world_id=game_loop.state.world_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.post("/game/input", response_model=GameInputResponse)
def submit_game_input(request: GameInputRequest) -> GameInputResponse:
    sync_runtime_settings()
    game_loop = get_session_store().get_session(request.session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {request.session_id}")

    try:
        result = game_loop.step(request.player_input)
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameInputResponse(
        narrative_text=result.narrative.text,
        suggested_actions=result.narrative.suggested_actions,
        visible_state=build_visible_state(result.state),
        turn=result.state.turn,
    )


@app.get("/game/state/{session_id}", response_model=GameStateResponse)
def get_game_state(session_id: str) -> GameStateResponse:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")

    return GameStateResponse(
        session_id=session_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.get("/game/{session_id}/graphs/relationships", response_model=RelationshipGraph)
def get_player_relationship_graph(session_id: str) -> RelationshipGraph:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_relationship_graph(game_loop.state, debug=False)


@app.get("/game/{session_id}/graphs/factions", response_model=FactionGraph)
def get_player_faction_graph(session_id: str) -> FactionGraph:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_faction_graph(game_loop.state, debug=False)


@app.get("/game/saves", response_model=SaveListResponse)
def list_saves(world_id: str | None = None) -> SaveListResponse:
    try:
        saves = get_save_repository().list_saves(world_id=world_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SaveListResponse(
        saves=[
            _save_summary_response(save)
            for save in saves
        ]
    )


def _save_summary_response(save: SaveGame) -> SaveSummaryResponse:
    state = GameState.model_validate_json(save.state_json)
    location = state.locations.get(state.player.location_id)
    return SaveSummaryResponse(
        save_id=save.save_id,
        world_id=state.world_id,
        world_name=_world_name_for_state(state),
        turn=state.turn,
        current_location_name=location.name if location else state.player.location_id,
        formatted_time=format_game_time(state),
        created_at=save.created_at.isoformat(),
        updated_at=save.updated_at.isoformat(),
        player_summary=f"Turn {state.turn} at {location.name if location else state.player.location_id}",
        enabled_mods=_enabled_mods_from_save(save),
    )


def _enabled_mods_from_save(save: SaveGame) -> dict[str, str]:
    try:
        payload = json.loads(save.enabled_mods)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, list):
        return {}
    result: dict[str, str] = {}
    for item in payload:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            result[item["id"]] = str(item.get("version", "unknown"))
    return result


def _world_name_for_state(state: GameState) -> str:
    try:
        pack = WorldLoader(get_worlds_root()).load(state.world_id)
    except Exception:
        return state.world_id
    return pack.manifest.name


@app.post("/game/{session_id}/save", response_model=SaveGameResponse)
def save_game(session_id: str) -> SaveGameResponse:
    sync_runtime_settings()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")

    save_id = str(uuid4())
    try:
        SaveService(get_save_repository()).save_game_loop(save_id, game_loop)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SaveGameResponse(
        save_id=save_id,
        session_id=session_id,
        world_id=game_loop.state.world_id,
        turn=game_loop.state.turn,
    )


@app.delete("/game/saves/{save_id}", response_model=DeleteSaveResponse)
def delete_save(save_id: str) -> DeleteSaveResponse:
    try:
        get_save_repository().delete_save(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DeleteSaveResponse(save_id=save_id)


@app.post("/game/load/{save_id}", response_model=LoadGameResponse)
def load_game(save_id: str) -> LoadGameResponse:
    sync_runtime_settings()
    repository = get_save_repository()
    try:
        state = repository.load_save(save_id)
        events = repository.list_events(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    session_id, game_loop = get_session_store().restore_session(state, events)
    return LoadGameResponse(
        save_id=save_id,
        session_id=session_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.get("/game/saves/{save_id}/migration-status", response_model=SaveMigrationStatusResponse)
def get_save_migration_status(save_id: str) -> SaveMigrationStatusResponse:
    return _get_save_migration_status(save_id)


@app.get("/saves/{save_id}/migration-status", response_model=SaveMigrationStatusResponse)
def get_save_migration_status_alias(save_id: str) -> SaveMigrationStatusResponse:
    return _get_save_migration_status(save_id)


def _get_save_migration_status(save_id: str) -> SaveMigrationStatusResponse:
    try:
        status = get_migration_service().status(
            save_id,
            available_mod_versions={
                mod.manifest.id: mod.manifest.version
                for mod in get_mod_loader().discover_mods()
            },
        )
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SaveMigrationStatusResponse(
        save_id=status.save_id,
        engine_version=status.engine_version,
        schema_version=status.schema_version,
        world_id=status.world_id,
        world_version=status.world_version,
        content_pack_version=status.content_pack_version,
        needs_migration=status.needs_migration,
        target_schema_version=status.target_schema_version,
        migration_path=[item.migration_id for item in status.migration_path],
        warnings=status.warnings,
    )


@app.post("/game/saves/{save_id}/migrate-dry-run", response_model=SaveMigrationResponse)
def dry_run_save_migration(save_id: str) -> SaveMigrationResponse:
    return _dry_run_save_migration(save_id)


@app.post("/saves/{save_id}/migrate-dry-run", response_model=SaveMigrationResponse)
def dry_run_save_migration_alias(save_id: str) -> SaveMigrationResponse:
    return _dry_run_save_migration(save_id)


def _dry_run_save_migration(save_id: str) -> SaveMigrationResponse:
    try:
        report = get_migration_service().dry_run(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _migration_response(report)


@app.post("/game/saves/{save_id}/migrate", response_model=SaveMigrationResponse)
def migrate_save(save_id: str) -> SaveMigrationResponse:
    return _migrate_save(save_id)


@app.post("/saves/{save_id}/migrate", response_model=SaveMigrationResponse)
def migrate_save_alias(save_id: str) -> SaveMigrationResponse:
    return _migrate_save(save_id)


def _migrate_save(save_id: str) -> SaveMigrationResponse:
    try:
        report = get_migration_service().apply(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _migration_response(report)


@app.get("/migrations", response_model=MigrationListResponse)
def list_migrations() -> MigrationListResponse:
    return MigrationListResponse(
        migrations=[
            MigrationInfoResponse(
                migration_id=migration.migration_id,
                source_version=migration.source_version,
                target_version=migration.target_version,
                description=migration.description,
            )
            for migration in get_migration_service().list_available_migrations()
        ]
    )


@app.get("/debug/sessions/{session_id}/events", response_model=DebugEventListResponse)
def get_debug_session_events(session_id: str) -> DebugEventListResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return DebugEventListResponse(
        events=[_debug_event_response(event) for event in game_loop.event_log.list_events()]
    )


@app.get("/debug/sessions/{session_id}/graphs/relationships", response_model=RelationshipGraph)
def get_debug_relationship_graph(session_id: str) -> RelationshipGraph:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_relationship_graph(game_loop.state, debug=True)


@app.get("/debug/sessions/{session_id}/graphs/factions", response_model=FactionGraph)
def get_debug_faction_graph(session_id: str) -> FactionGraph:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_faction_graph(game_loop.state, debug=True)


@app.get("/debug/saves/{save_id}/events", response_model=DebugEventListResponse)
def get_debug_save_events(save_id: str) -> DebugEventListResponse:
    require_debug_api()
    try:
        events = get_save_repository().list_events(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DebugEventListResponse(
        events=[_debug_event_response(event) for event in events]
    )


@app.get("/debug/performance/recent", response_model=DebugPerformanceRecentResponse)
def get_debug_performance_recent(limit: int = 50) -> DebugPerformanceRecentResponse:
    require_debug_api()
    recorder = get_performance_recorder()
    return DebugPerformanceRecentResponse(
        enabled=performance_logging_enabled(),
        samples=[
            DebugPerformanceSampleResponse(
                sample_id=sample.sample_id,
                name=sample.name,
                duration_ms=sample.duration_ms,
                started_at=sample.started_at.isoformat(),
                stage_durations_ms=sample.stage_durations_ms,
                tags=sample.tags,
            )
            for sample in recorder.recent(limit)
        ],
    )


@app.get("/debug/performance/summary", response_model=DebugPerformanceSummaryResponse)
def get_debug_performance_summary() -> DebugPerformanceSummaryResponse:
    require_debug_api()
    summary = get_performance_recorder().summary()
    return DebugPerformanceSummaryResponse(
        enabled=summary.enabled,
        sample_count=summary.sample_count,
        entries=[
            DebugPerformanceSummaryEntryResponse(
                name=entry.name,
                count=entry.count,
                total_duration_ms=entry.total_duration_ms,
                average_duration_ms=entry.average_duration_ms,
                max_duration_ms=entry.max_duration_ms,
            )
            for entry in summary.entries
        ],
    )


@app.get("/evals/narrative/recent", response_model=NarrativeEvalRecentResponse)
def get_recent_narrative_evals() -> NarrativeEvalRecentResponse:
    require_debug_api()
    return NarrativeEvalRecentResponse(
        reports=[_narrative_eval_report_response(report) for report in get_narrative_eval_reports()[-10:]]
    )


@app.post("/evals/narrative/run", response_model=NarrativeEvalReportResponse)
def run_narrative_evals() -> NarrativeEvalReportResponse:
    require_debug_api()
    report = run_narrative_quality_evals(sample_narrative_quality_cases())
    get_narrative_eval_reports().append(report)
    return _narrative_eval_report_response(report)


@app.get("/evals/narrative/{run_id}", response_model=NarrativeEvalReportResponse)
def get_narrative_eval(run_id: str) -> NarrativeEvalReportResponse:
    require_debug_api()
    for report in get_narrative_eval_reports():
        if report.run_id == run_id:
            return _narrative_eval_report_response(report)
    raise HTTPException(status_code=404, detail=f"Narrative eval run not found: {run_id}")


@app.get("/playtests/recent", response_model=PlaytestRecentResponse)
def get_recent_playtests() -> PlaytestRecentResponse:
    require_playtest_api()
    return PlaytestRecentResponse(reports=get_playtest_reports()[-10:])


@app.post("/playtests/run", response_model=PlaytestReportResponse)
def run_playtest_api(request: PlaytestRunRequest) -> PlaytestReportResponse:
    require_playtest_api()
    try:
        with TemporaryDirectory(prefix="llm_world_playtest_", ignore_cleanup_errors=True) as temp_dir:
            options = PlaytestOptions(
                world_id=request.world_id,
                strategy=request.agent_type,
                max_steps=request.steps,
                seed=request.seed,
                save_every=1 if request.save_load_check and request.steps > 0 else None,
                database_path=str(Path(temp_dir) / "playtest.db") if request.save_load_check else None,
                worlds_root=get_worlds_root(),
            )
            report = run_playtest(options)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorldLoaderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response = _playtest_report_response(report, steps_requested=request.steps)
    get_playtest_reports().append(response)
    return response


@app.get("/playtests/{run_id}", response_model=PlaytestReportResponse)
def get_playtest(run_id: str) -> PlaytestReportResponse:
    require_playtest_api()
    for report in get_playtest_reports():
        if report.run_id == run_id:
            return report
    raise HTTPException(status_code=404, detail=f"Playtest run not found: {run_id}")


def _playtest_report_response(report: PlaytestReport, steps_requested: int) -> PlaytestReportResponse:
    return PlaytestReportResponse(
        run_id=f"playtest-{uuid4()}",
        created_at=datetime.now(UTC).isoformat(),
        agent_type=report.strategy,
        world_id=report.world_id,
        seed=report.seed,
        steps_requested=steps_requested,
        turns_run=report.turns_run,
        actions_taken=[action.model_dump(mode="json") for action in report.actions_taken],
        errors=[_safe_report_text(value) for value in report.errors],
        invariant_violations=[_safe_report_text(value) for value in report.invariant_violations],
        visibility_leaks=[_safe_report_text(value) for value in report.visibility_leaks],
        save_load_failures=[_safe_report_text(value) for value in report.save_load_failures],
        final_state_summary=report.final_state_summary.model_dump(mode="json"),
    )


def _safe_report_text(value: str) -> str:
    return (
        re.sub(r":forbidden:(?:\[[^\]]+\]|[^,\]\s]+)", ":forbidden:[redacted]", value)
        .replace("forbidden hidden text", "[hidden text redacted]")
        .replace("sk-", "sk-[redacted]-")
    )


def _narrative_eval_report_response(report: NarrativeQualityReport) -> NarrativeEvalReportResponse:
    return NarrativeEvalReportResponse(
        run_id=report.run_id,
        created_at=report.created_at,
        total_cases=report.total_cases,
        passed=report.passed,
        failed=report.failed,
        skipped=report.skipped,
        failure_reasons={
            case_id: [_safe_report_text(reason) for reason in reasons]
            for case_id, reasons in report.failure_reasons.items()
        },
        categories=report.categories,
        case_results=[
            NarrativeEvalCaseResultResponse(
                case_id=result.case_id,
                category=result.category,
                passed=result.passed,
                skipped=result.skipped,
                failure_reasons=[_safe_report_text(reason) for reason in result.failure_reasons],
            )
            for result in report.case_results
        ],
    )


def _debug_event_response(event: Event) -> DebugEventResponse:
    return DebugEventResponse(
        turn=event.turn,
        event_id=event.event_id,
        actor_id=event.actor_id,
        action_type=event.action_type,
        result=event.result,
        state_deltas=event.state_deltas,
        visible_to_player=event.visible_to_player,
        created_at=event.created_at.isoformat(),
    )


def _migration_response(report: object) -> SaveMigrationResponse:
    return SaveMigrationResponse(
        save_id=getattr(report, "save_id"),
        source_version=getattr(report, "source_version"),
        target_version=getattr(report, "target_version"),
        dry_run=getattr(report, "dry_run"),
        backup_save_id=getattr(report, "backup_save_id"),
        success=getattr(report, "success"),
        warnings=getattr(report, "warnings"),
        applied_migrations=[
            MigrationHistoryEntryResponse(
                migration_id=entry.migration_id,
                source_version=entry.source_version,
                target_version=entry.target_version,
                description=entry.description,
                applied_at=entry.applied_at,
            )
            for entry in getattr(report, "applied_migrations")
        ],
    )


@app.get("/authoring/worlds", response_model=AuthoringWorldListResponse)
def list_authoring_worlds() -> AuthoringWorldListResponse:
    require_authoring_api()
    service = get_authoring_service()
    return AuthoringWorldListResponse(
        worlds=[_authoring_world_response(world) for world in service.list_worlds()]
    )


@app.post("/authoring/worlds", response_model=AuthoringCreateWorldResponse)
def create_authoring_world(request: AuthoringCreateWorldRequest) -> AuthoringCreateWorldResponse:
    require_authoring_api()
    try:
        world, report = get_authoring_service().create_world(
            request.world_id,
            request.name,
            request.description,
            request.start_location_id,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringCreateWorldResponse(
        world=_authoring_world_response(world),
        validation=_authoring_validation_response(report),
    )


@app.get("/authoring/worlds/{world_id}", response_model=AuthoringWorldDetailResponse)
def get_authoring_world(world_id: str) -> AuthoringWorldDetailResponse:
    require_authoring_api()
    service = get_authoring_service()
    try:
        world = service.get_world_summary(world_id)
        report = service.validate_world(world_id)
        files = service.list_files(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthoringWorldDetailResponse(
        world=_authoring_world_response(world),
        files=files,
        validation=_authoring_validation_response(report),
    )


@app.get("/authoring/worlds/{world_id}/files", response_model=AuthoringFileListResponse)
def list_authoring_files(world_id: str) -> AuthoringFileListResponse:
    require_authoring_api()
    try:
        files = get_authoring_service().list_files(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthoringFileListResponse(world_id=world_id, files=files)


@app.get("/authoring/worlds/{world_id}/files/{file_name}", response_model=AuthoringFileResponse)
def read_authoring_file(world_id: str, file_name: str) -> AuthoringFileResponse:
    require_authoring_api()
    try:
        content = get_authoring_service().read_file(world_id, file_name)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringFileResponse(world_id=world_id, file_name=file_name, content=content)


@app.put("/authoring/worlds/{world_id}/files/{file_name}", response_model=AuthoringFileWriteResponse)
def write_authoring_file(
    world_id: str,
    file_name: str,
    request: AuthoringFileWriteRequest,
) -> AuthoringFileWriteResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().write_file(world_id, file_name, request.content)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not report.ok:
        raise HTTPException(
            status_code=400,
            detail=_authoring_validation_response(report).model_dump(mode="json"),
        )
    return AuthoringFileWriteResponse(
        world_id=world_id,
        file_name=file_name,
        validation=_authoring_validation_response(report),
    )


@app.post(
    "/authoring/worlds/{world_id}/preview-file-change",
    response_model=AuthoringFilePreviewResponse,
)
def preview_authoring_file_change(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringFilePreviewResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().preview_file_change(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_preview_response(world_id, request.file_name, report)


@app.post(
    "/authoring/worlds/{world_id}/validate-draft",
    response_model=AuthoringValidationResponse,
)
def validate_authoring_draft(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringValidationResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_draft(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_validation_response(report)


@app.post(
    "/authoring/worlds/{world_id}/impact-analysis",
    response_model=AuthoringImpactAnalysisResponse,
)
def analyze_authoring_draft_impact(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringImpactAnalysisResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().analyze_file_impact(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_impact_response(report)


@app.post("/authoring/worlds/{world_id}/validate", response_model=AuthoringValidationResponse)
def validate_authoring_world(world_id: str) -> AuthoringValidationResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_world(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _authoring_validation_response(report)


@app.get("/authoring/templates", response_model=ScenarioTemplateListResponse)
def list_authoring_templates() -> ScenarioTemplateListResponse:
    require_authoring_api()
    try:
        templates = get_scenario_template_renderer().list_templates()
    except ScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ScenarioTemplateListResponse(
        templates=[_scenario_template_response(template) for template in templates]
    )


@app.post("/authoring/templates/{template_id}/preview", response_model=ScenarioTemplatePreviewResponse)
def preview_authoring_template(
    template_id: str,
    request: ScenarioTemplateRenderRequest,
) -> ScenarioTemplatePreviewResponse:
    require_authoring_api()
    try:
        preview = get_scenario_template_renderer().preview_template(
            template_id,
            request.variables,
            target_world_id=request.target_world_id,
        )
    except ScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _scenario_template_preview_response(preview)


@app.post("/authoring/templates/{template_id}/render", response_model=RenderedScenarioTemplateResponse)
def render_authoring_template(
    template_id: str,
    request: ScenarioTemplateRenderRequest,
) -> RenderedScenarioTemplateResponse:
    require_authoring_api()
    try:
        template = get_scenario_template_renderer().get_template(template_id)
        rendered = get_scenario_template_renderer().render_template(template, request.variables)
    except ScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _rendered_template_response(rendered)


@app.get("/authoring/worlds/{world_id}/quests/graph", response_model=QuestGraphResponse)
def get_authoring_quest_graph(world_id: str) -> QuestGraphResponse:
    require_authoring_api()
    try:
        graph = parse_quest_graph(world_id, get_authoring_service())
    except (AuthoringError, QuestGraphError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _quest_graph_response(graph)


@app.post("/authoring/worlds/{world_id}/quests/graph/preview", response_model=QuestGraphPreviewResponse)
def preview_authoring_quest_graph(
    world_id: str,
    request: QuestGraphPreviewRequest,
) -> QuestGraphPreviewResponse:
    require_authoring_api()
    try:
        graph = QuestGraph.model_validate(request.graph.model_dump(mode="json", exclude={"local_only"}))
        preview = preview_quest_graph(world_id, graph, get_authoring_service())
        validation = get_authoring_service().validate_draft(world_id, "quests.yaml", preview.yaml_content)
    except (AuthoringError, QuestGraphError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QuestGraphPreviewResponse(
        world_id=world_id,
        graph=_quest_graph_response(preview.graph),
        yaml_content=preview.yaml_content,
        validation=_authoring_validation_response(validation),
    )


@app.get("/authoring/mods", response_model=AuthoringModListResponse)
def list_authoring_mods() -> AuthoringModListResponse:
    require_authoring_api()
    try:
        mods = get_mod_loader().discover_mods()
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringModListResponse(mods=[_authoring_mod_response(mod) for mod in mods])


@app.get("/authoring/mods/load-order", response_model=AuthoringModLoadOrderResponse)
def get_authoring_mod_load_order() -> AuthoringModLoadOrderResponse:
    require_authoring_api()
    try:
        report = get_mod_loader().resolve_load_order()
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringModLoadOrderResponse(
        ok=report.ok,
        load_order=report.load_order,
        errors=report.errors,
    )


@app.get("/authoring/mods/{mod_id}", response_model=AuthoringModDetailResponse)
def get_authoring_mod(mod_id: str) -> AuthoringModDetailResponse:
    require_authoring_api()
    try:
        mod = next((item for item in get_mod_loader().discover_mods() if item.manifest.id == mod_id), None)
        if mod is None:
            raise ModLoaderError(f"Mod not found: {mod_id}")
        validation = get_mod_loader().validate_mod(mod_id)
    except ModLoaderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthoringModDetailResponse(
        mod=_authoring_mod_response(mod),
        validation=_authoring_mod_validation_response(validation),
    )


@app.post("/authoring/mods/{mod_id}/validate", response_model=AuthoringModValidationResponse)
def validate_authoring_mod(mod_id: str) -> AuthoringModValidationResponse:
    require_authoring_api()
    try:
        report = get_mod_loader().validate_mod(mod_id)
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_mod_validation_response(report)


@app.get("/authoring/export/worlds/{world_id}", response_model=ArchiveExportResponse)
def export_authoring_world(world_id: str) -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_import_export_service().export_world(world_id)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type="world", id=world_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.post("/authoring/import/worlds", response_model=ArchiveImportResponse)
def import_authoring_world(request: ArchiveImportRequest) -> ArchiveImportResponse:
    require_authoring_api()
    try:
        result = get_import_export_service().import_world(request.archive_base64, overwrite=request.overwrite)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveImportResponse(**result.model_dump(mode="json"))


@app.get("/authoring/export/mods/{mod_id}", response_model=ArchiveExportResponse)
def export_authoring_mod(mod_id: str) -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_import_export_service().export_mod(mod_id)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type="mod", id=mod_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.post("/authoring/import/mods", response_model=ArchiveImportResponse)
def import_authoring_mod(request: ArchiveImportRequest) -> ArchiveImportResponse:
    require_authoring_api()
    try:
        result = get_import_export_service().import_mod(request.archive_base64, overwrite=request.overwrite)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveImportResponse(**result.model_dump(mode="json"))


@app.get("/authoring/export/saves/{save_id}", response_model=ArchiveExportResponse)
def export_authoring_save(save_id: str) -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_import_export_service().export_save(save_id)
    except (ImportExportError, SaveRepositoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type="save", id=save_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.post("/authoring/import/saves", response_model=ArchiveImportResponse)
def import_authoring_save(request: ArchiveImportRequest) -> ArchiveImportResponse:
    require_authoring_api()
    try:
        result = get_import_export_service().import_save(request.archive_base64, overwrite=request.overwrite)
    except (ImportExportError, SaveRepositoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveImportResponse(**result.model_dump(mode="json"))


def _authoring_world_response(world: object) -> AuthoringWorldSummaryResponse:
    return AuthoringWorldSummaryResponse(
        world_id=getattr(world, "world_id"),
        name=getattr(world, "name"),
        description=getattr(world, "description"),
        version=getattr(world, "version"),
        file_count=getattr(world, "file_count"),
    )


def _authoring_mod_response(mod: ModInfo) -> AuthoringModSummaryResponse:
    manifest = mod.manifest
    return AuthoringModSummaryResponse(
        id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        engine_version_min=manifest.engine_version_min,
        engine_version_max=manifest.engine_version_max,
        content_schema_version=manifest.content_schema_version,
        dependencies=manifest.dependencies,
        optional_dependencies=manifest.optional_dependencies,
        conflicts=manifest.conflicts,
        load_order_hint=manifest.load_order_hint,
        compatible_worlds=manifest.compatible_worlds,
        migration_notes=manifest.migration_notes,
        entry_worlds=manifest.entry_worlds,
        content_paths=manifest.content_paths,
        author=manifest.author,
        description=manifest.description,
    )


def _authoring_mod_validation_response(report: ModValidationReport) -> AuthoringModValidationResponse:
    return AuthoringModValidationResponse(
        mod_id=report.mod_id,
        ok=report.ok,
        errors=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.errors
        ],
        warnings=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.warnings
        ],
        suggestions=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.suggestions
        ],
        world_report_ids=sorted(report.world_reports),
    )


def _scenario_template_response(template: ScenarioTemplate) -> ScenarioTemplateResponse:
    return ScenarioTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        template_type=template.template_type.value,
        required_variables=template.required_variables,
        optional_variables=template.optional_variables,
        output_files=[
            ScenarioTemplateOutputFileResponse(
                file_name=output_file.file_name,
                content=output_file.content,
            )
            for output_file in template.output_files
        ],
        validation_rules=template.validation_rules,
        tags=template.tags,
    )


def _rendered_template_response(rendered: RenderedTemplate) -> RenderedScenarioTemplateResponse:
    return RenderedScenarioTemplateResponse(
        template_id=rendered.template_id,
        template_type=rendered.template_type.value,
        files=[
            RenderedScenarioTemplateFileResponse(
                file_name=rendered_file.file_name,
                content=rendered_file.content,
            )
            for rendered_file in rendered.files
        ],
    )


def _scenario_template_preview_response(preview: ScenarioTemplatePreview) -> ScenarioTemplatePreviewResponse:
    return ScenarioTemplatePreviewResponse(
        template=_scenario_template_response(preview.template),
        rendered=_rendered_template_response(preview.rendered),
        validation_report=(
            _authoring_validation_response(preview.validation_report)
            if preview.validation_report is not None
            else None
        ),
        writes_to_disk=preview.writes_to_disk,
    )


def _quest_graph_response(graph: QuestGraph) -> QuestGraphResponse:
    return QuestGraphResponse.model_validate(graph.model_dump(mode="json"))


def _authoring_preview_response(
    world_id: str,
    file_name: str,
    report: object,
) -> AuthoringFilePreviewResponse:
    return AuthoringFilePreviewResponse(
        world_id=world_id,
        file_name=file_name,
        parsed_ok=getattr(report, "parsed_ok"),
        validation_report=_authoring_validation_response(getattr(report, "validation_report")),
        normalized_yaml=getattr(report, "normalized_yaml"),
        diff_summary=AuthoringDiffSummaryResponse.model_validate(
            getattr(report, "diff_summary").model_dump(mode="json")
        ),
        affected_refs=getattr(report, "affected_refs"),
        potential_save_migration_required=getattr(
            report,
            "potential_save_migration_required",
        ),
        impact=_authoring_impact_response(getattr(report, "impact")),
    )


def _authoring_impact_response(report: object) -> AuthoringImpactAnalysisResponse:
    return AuthoringImpactAnalysisResponse.model_validate(report.model_dump(mode="json"))


def _authoring_validation_response(report: ValidationReport) -> AuthoringValidationResponse:
    return AuthoringValidationResponse(
        world_id=report.world_id,
        ok=report.ok,
        errors=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.errors
        ],
        warnings=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.warnings
        ],
        suggestions=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.suggestions
        ],
    )
