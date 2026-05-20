from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.db.migrations import CURRENT_ENGINE_VERSION


WorkspaceSafeStatus = Literal["ok", "missing", "invalid", "unsafe_path"]
WorkspaceTemplateType = Literal[
    "blank_studio",
    "novel_project",
    "world_project",
    "RP_project",
    "script_package_project",
    "module_development_project",
    "campaign_project",
]


class ProjectWorkspace(BaseModel):
    workspace_id: str
    name: str
    path_redacted: str
    world_count: int = 0
    last_opened_at: str | None = None
    engine_version: str = CURRENT_ENGINE_VERSION
    schema_version: str = CURRENT_GAME_STATE_SCHEMA_VERSION
    safe_status: WorkspaceSafeStatus = "ok"


class RecentProjectEntry(BaseModel):
    workspace_id: str
    display_name: str
    path_redacted: str
    last_opened_at: str
    last_world_id: str | None = None
    safe_status: WorkspaceSafeStatus = "ok"


class WorkspaceListResponse(BaseModel):
    local_only: bool = True
    workspaces: list[ProjectWorkspace] = Field(default_factory=list)


class RecentProjectsResponse(BaseModel):
    local_only: bool = True
    projects: list[RecentProjectEntry] = Field(default_factory=list)


class WorkspaceTemplate(BaseModel):
    template_id: WorkspaceTemplateType
    name: str
    description: str
    directories: list[str]
    default_config_template: str
    starter_world: bool = False
    docs_links: list[str] = Field(default_factory=list)
    recommended_workflow_presets: list[str] = Field(default_factory=list)


class WorkspaceTemplateListResponse(BaseModel):
    local_only: bool = True
    templates: list[WorkspaceTemplate] = Field(default_factory=list)


class WorkspaceAddRequest(BaseModel):
    path: str
    name: str | None = None


class WorkspaceCreateFromTemplateRequest(BaseModel):
    template_id: WorkspaceTemplateType
    path: str
    name: str | None = None


class WorkspaceSelectRequest(BaseModel):
    workspace_id: str
    last_world_id: str | None = None


class RecentProjectsService:
    """Bounded local recent-project list.

    Entries are safe summaries only. Raw paths, env values, API keys, and
    GameState are never stored here.
    """

    def __init__(self, *, max_entries: int = 12) -> None:
        self.max_entries = max_entries
        self._entries: dict[str, RecentProjectEntry] = {}

    def record_opened_project(self, workspace: ProjectWorkspace, *, last_world_id: str | None = None) -> RecentProjectEntry:
        entry = RecentProjectEntry(
            workspace_id=workspace.workspace_id,
            display_name=workspace.name,
            path_redacted=workspace.path_redacted,
            last_opened_at=workspace.last_opened_at or datetime.now(UTC).isoformat(),
            last_world_id=last_world_id,
            safe_status=workspace.safe_status,
        )
        _ensure_safe_recent_entry(entry)
        self._entries[entry.workspace_id] = entry
        self._trim()
        return entry

    def list_recent_projects(self) -> list[RecentProjectEntry]:
        return sorted(self._entries.values(), key=lambda item: item.last_opened_at, reverse=True)

    def clear_recent_projects(self) -> None:
        self._entries.clear()

    def remove_recent_project(self, workspace_id: str) -> bool:
        return self._entries.pop(workspace_id, None) is not None

    def _trim(self) -> None:
        ordered = self.list_recent_projects()
        for entry in ordered[self.max_entries :]:
            self._entries.pop(entry.workspace_id, None)


class WorkspaceService:
    """Local project registry for Desktop Studio.

    The service stores workspace references only. It does not import content,
    read secret config, mutate GameState, or change active saves.
    """

    def __init__(self, *, default_workspace: str | Path = ".") -> None:
        self._workspaces: dict[str, tuple[Path, ProjectWorkspace]] = {}
        self._current_workspace_id: str | None = None
        self.add_workspace(str(default_workspace), name="Current Workspace")
        if self._workspaces:
            self._current_workspace_id = next(iter(self._workspaces))

    def list_workspaces(self) -> list[ProjectWorkspace]:
        self._refresh_all()
        return sorted((workspace for _, workspace in self._workspaces.values()), key=lambda item: item.name.lower())

    def add_workspace(self, path: str, name: str | None = None) -> ProjectWorkspace:
        candidate = _resolve_workspace_path(path)
        workspace_id = _workspace_id(candidate)
        workspace = _workspace_summary(candidate, name=name)
        self._workspaces[workspace_id] = (candidate, workspace)
        if self._current_workspace_id is None:
            self._current_workspace_id = workspace_id
        return workspace

    def remove_workspace_reference(self, workspace_id: str) -> bool:
        if workspace_id not in self._workspaces:
            return False
        del self._workspaces[workspace_id]
        if self._current_workspace_id == workspace_id:
            self._current_workspace_id = next(iter(self._workspaces), None)
        return True

    def select_workspace(self, workspace_id: str, *, last_world_id: str | None = None) -> ProjectWorkspace:
        if workspace_id not in self._workspaces:
            raise ValueError(f"Unknown workspace: {workspace_id}")
        path, workspace = self._workspaces[workspace_id]
        workspace = _workspace_summary(path, name=workspace.name, last_opened_at=datetime.now(UTC).isoformat())
        self._workspaces[workspace_id] = (path, workspace)
        self._current_workspace_id = workspace_id
        return workspace

    def get_current_workspace(self) -> ProjectWorkspace | None:
        if self._current_workspace_id is None:
            return None
        item = self._workspaces.get(self._current_workspace_id)
        if item is None:
            return None
        path, workspace = item
        refreshed = _workspace_summary(path, name=workspace.name, last_opened_at=workspace.last_opened_at)
        self._workspaces[self._current_workspace_id] = (path, refreshed)
        return refreshed

    def list_templates(self) -> list[WorkspaceTemplate]:
        return list(_workspace_templates().values())

    def create_from_template(self, request: WorkspaceCreateFromTemplateRequest) -> ProjectWorkspace:
        templates = _workspace_templates()
        template = templates.get(request.template_id)
        if template is None:
            raise ValueError(f"Unknown workspace template: {request.template_id}")
        target = _resolve_new_workspace_path(request.path)
        target.mkdir(parents=True, exist_ok=False)
        for directory in template.directories:
            _safe_template_relative_path(directory)
            (target / directory).mkdir(parents=True, exist_ok=True)
        _write_safe_starter_files(target, template)
        workspace = self.add_workspace(str(target), name=request.name or template.name)
        self._current_workspace_id = workspace.workspace_id
        return workspace

    def _refresh_all(self) -> None:
        for workspace_id, (path, workspace) in list(self._workspaces.items()):
            self._workspaces[workspace_id] = (
                path,
                _workspace_summary(path, name=workspace.name, last_opened_at=workspace.last_opened_at),
            )


def _resolve_workspace_path(raw_path: str) -> Path:
    if not raw_path or not raw_path.strip():
        raise ValueError("Workspace path is required.")
    normalized = raw_path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    lowered_parts = {part.lower() for part in parts}
    if ".." in parts or ".env" in lowered_parts or "node_modules" in lowered_parts:
        raise ValueError("Workspace path is not allowed.")
    path = Path(raw_path).expanduser().resolve()
    if path.name.lower().startswith(".env"):
        raise ValueError("Workspace path cannot point at environment files.")
    if not path.exists():
        raise ValueError("Workspace path does not exist.")
    if not path.is_dir():
        raise ValueError("Workspace path must be a directory.")
    return path


def _resolve_new_workspace_path(raw_path: str) -> Path:
    if not raw_path or not raw_path.strip():
        raise ValueError("Workspace path is required.")
    normalized = raw_path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    lowered_parts = {part.lower() for part in parts}
    forbidden = {".env", "node_modules", "dist", "logs", "cache", "__pycache__"}
    if ".." in parts or lowered_parts.intersection(forbidden):
        raise ValueError("Workspace path is not allowed.")
    path = Path(raw_path).expanduser().resolve()
    if path.name.lower().startswith(".env"):
        raise ValueError("Workspace path cannot point at environment files.")
    if not path.parent.exists() or not path.parent.is_dir():
        raise ValueError("Workspace parent directory does not exist.")
    if path.exists() and any(path.iterdir()):
        raise ValueError("Workspace path already exists and is not empty.")
    return path


def _workspace_id(path: Path) -> str:
    safe = path.as_posix().lower().replace(":", "").replace("/", "_").strip("_")
    return safe[-96:] or "workspace"


def _workspace_summary(path: Path, *, name: str | None = None, last_opened_at: str | None = None) -> ProjectWorkspace:
    exists = path.exists() and path.is_dir()
    status: WorkspaceSafeStatus = "ok" if exists else "missing"
    return ProjectWorkspace(
        workspace_id=_workspace_id(path),
        name=(name or path.name or "Workspace").strip(),
        path_redacted=_redact_path(path),
        world_count=_count_worlds(path) if exists else 0,
        last_opened_at=last_opened_at,
        safe_status=status,
    )


def _count_worlds(path: Path) -> int:
    worlds_root = path / "worlds"
    if not worlds_root.exists() or not worlds_root.is_dir():
        return 0
    count = 0
    for child in worlds_root.iterdir():
        if child.is_dir() and (child / "manifest.yaml").exists():
            count += 1
    return count


def _workspace_templates() -> dict[WorkspaceTemplateType, WorkspaceTemplate]:
    common_docs = ["README.md", "docs/DESKTOP_STUDIO_BOUNDARY.md", "docs/V1_7_ROADMAP.md"]
    return {
        "blank_studio": WorkspaceTemplate(
            template_id="blank_studio",
            name="Blank Studio",
            description="Minimal local workspace with standard folders and safe config template.",
            directories=["worlds", "saves", "templates", "modules", "packages", "docs"],
            default_config_template=_safe_workspace_config_template(),
            docs_links=common_docs,
            recommended_workflow_presets=["import_review", "pre_release_check"],
        ),
        "novel_project": WorkspaceTemplate(
            template_id="novel_project",
            name="Interactive Novel Project",
            description="Workspace for a focused interactive fiction world and authoring drafts.",
            directories=["worlds", "saves", "templates", "character_packs", "scenario_suites", "docs"],
            default_config_template=_safe_workspace_config_template(),
            starter_world=True,
            docs_links=common_docs + ["docs/WORLD_ENGINE.md"],
            recommended_workflow_presets=["new_world", "new_questline"],
        ),
        "world_project": WorkspaceTemplate(
            template_id="world_project",
            name="World Project",
            description="Workspace for larger world pack production with content and quality folders.",
            directories=["worlds", "saves", "templates", "content_library", "scenario_suites", "quality_reports", "docs"],
            default_config_template=_safe_workspace_config_template(),
            starter_world=True,
            docs_links=common_docs + ["docs/CONTENT_PRODUCTION_BOUNDARY.md"],
            recommended_workflow_presets=["new_world", "pre_release_check"],
        ),
        "RP_project": WorkspaceTemplate(
            template_id="RP_project",
            name="RP Project",
            description="Workspace for RP profiles, character packs, voices, and dialogue scenes.",
            directories=["worlds", "character_packs", "rp_profiles", "voice_profiles", "dialogue_scenes", "docs"],
            default_config_template=_safe_workspace_config_template(),
            starter_world=True,
            docs_links=common_docs + ["docs/ROLEPLAY_BOUNDARY.md"],
            recommended_workflow_presets=["new_character_pack", "new_rp_scene"],
        ),
        "script_package_project": WorkspaceTemplate(
            template_id="script_package_project",
            name="Script Package Project",
            description="Workspace for assembling local script packages and scenario regression drafts.",
            directories=["script_packages", "quest_packs", "character_packs", "templates", "scenario_suites", "docs"],
            default_config_template=_safe_workspace_config_template(),
            docs_links=common_docs + ["docs/CONTENT_PACKS.md"],
            recommended_workflow_presets=["import_review", "pre_release_check"],
        ),
        "module_development_project": WorkspaceTemplate(
            template_id="module_development_project",
            name="Module Development Project",
            description="Workspace for declarative gameplay modules and action mods.",
            directories=["modules", "action_mods", "quality_tests", "regression_scenarios", "docs"],
            default_config_template=_safe_workspace_config_template(),
            docs_links=common_docs + ["docs/GAMEPLAY_MODULE_BOUNDARY.md"],
            recommended_workflow_presets=["branch_merge_review", "pre_release_check"],
        ),
        "campaign_project": WorkspaceTemplate(
            template_id="campaign_project",
            name="Campaign Project",
            description="Workspace for campaign starter kits, NPC packs, quest packs, and quality gates.",
            directories=["worlds", "campaign_starters", "script_packages", "npc_packs", "quest_packs", "scenario_suites", "docs"],
            default_config_template=_safe_workspace_config_template(),
            starter_world=True,
            docs_links=common_docs + ["docs/CONTENT_PRODUCTION_BOUNDARY.md"],
            recommended_workflow_presets=["new_world", "new_mystery_case", "pre_release_check"],
        ),
    }


def _safe_workspace_config_template() -> str:
    return "\n".join(
        [
            "# Safe local workspace config template.",
            "# Do not put API keys in this file.",
            'LLM_PROVIDER="mock"',
            'VITE_API_BASE_URL="http://127.0.0.1:8000"',
            "",
        ]
    )


def _safe_template_relative_path(raw_path: str) -> None:
    path = Path(raw_path)
    lowered = raw_path.lower().replace("\\", "/")
    forbidden = (".env", "..", "node_modules", "dist", "logs", "cache", "__pycache__")
    if path.is_absolute() or any(token in lowered.split("/") for token in forbidden):
        raise ValueError("Template contains unsafe path.")


def _write_safe_starter_files(target: Path, template: WorkspaceTemplate) -> None:
    (target / "README.md").write_text(
        f"# {template.name}\n\n{template.description}\n\nThis local workspace template contains no API keys or executable scripts.\n",
        encoding="utf-8",
    )
    (target / "config.template.env").write_text(template.default_config_template, encoding="utf-8")
    if template.starter_world:
        world_id = "starter_world"
        world_root = target / "worlds" / world_id
        world_root.mkdir(parents=True, exist_ok=True)
        (world_root / "manifest.yaml").write_text(
            "id: starter_world\nname: Starter World\nversion: 0.1.0\n",
            encoding="utf-8",
        )


def _redact_path(path: Path) -> str:
    parts = path.parts
    if len(parts) <= 2:
        return path.name or path.as_posix()
    return f"{parts[0]}...{parts[-2]}/{parts[-1]}".replace("\\", "/")


def _ensure_safe_recent_entry(entry: RecentProjectEntry) -> None:
    serialized = entry.model_dump_json().lower()
    forbidden = ("api_key", "llm_api_key", "openai_api_key", "raw_env", "sk-", ".env")
    if any(token in serialized for token in forbidden):
        raise ValueError("Recent project entry contains sensitive data.")
