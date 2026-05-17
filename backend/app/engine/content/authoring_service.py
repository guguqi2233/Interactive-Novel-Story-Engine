from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from app.engine.content.validator import ValidationReport, validate_world_pack
from app.engine.content.world_loader import WorldManifest


ALLOWED_AUTHORING_FILES: tuple[str, ...] = (
    "manifest.yaml",
    "locations.yaml",
    "npcs.yaml",
    "items.yaml",
    "quests.yaml",
    "facts.yaml",
    "factions.yaml",
    "rumors.yaml",
    "relationships.yaml",
)

LIST_FILE_KEYS: dict[str, str] = {
    "locations.yaml": "locations",
    "npcs.yaml": "npcs",
    "items.yaml": "items",
    "quests.yaml": "quests",
    "facts.yaml": "facts",
    "factions.yaml": "factions",
    "rumors.yaml": "rumors",
    "relationships.yaml": "relationships",
}


class AuthoringError(ValueError):
    """Raised when local authoring input is invalid or unsafe."""


class AuthoringWorldSummary(BaseModel):
    world_id: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    file_count: int = 0


class ContentAuthoringService:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root)

    def list_worlds(self) -> list[AuthoringWorldSummary]:
        if not self.worlds_root.exists():
            return []
        worlds: list[AuthoringWorldSummary] = []
        for world_path in sorted(self.worlds_root.iterdir(), key=lambda path: path.name):
            if world_path.is_dir():
                worlds.append(self.get_world_summary(world_path.name))
        return worlds

    def get_world_summary(self, world_id: str) -> AuthoringWorldSummary:
        world_path = self._safe_world_path(world_id)
        manifest = self._read_manifest(world_path / "manifest.yaml")
        existing_files = [name for name in ALLOWED_AUTHORING_FILES if (world_path / name).exists()]
        return AuthoringWorldSummary(
            world_id=world_id,
            name=manifest.name if manifest else None,
            description=manifest.description if manifest else "",
            version=manifest.version if manifest else None,
            file_count=len(existing_files),
        )

    def list_files(self, world_id: str) -> list[str]:
        world_path = self._safe_world_path(world_id)
        return [name for name in ALLOWED_AUTHORING_FILES if (world_path / name).exists()]

    def read_file(self, world_id: str, file_name: str) -> str:
        path = self._safe_file_path(world_id, file_name)
        if not path.exists():
            raise AuthoringError(f"Content file not found: {file_name}")
        return path.read_text(encoding="utf-8")

    def write_file(self, world_id: str, file_name: str, content: str) -> ValidationReport:
        path = self._safe_file_path(world_id, file_name)
        self._parse_yaml(content, file_name)
        previous_content = path.read_text(encoding="utf-8") if path.exists() else None
        path.write_text(content, encoding="utf-8")
        report = self.validate_world(world_id)
        if not report.ok:
            if previous_content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(previous_content, encoding="utf-8")
        return report

    def validate_world(self, world_id: str) -> ValidationReport:
        self._safe_world_path(world_id)
        return validate_world_pack(world_id, worlds_root=self.worlds_root)

    def create_world(
        self,
        world_id: str,
        name: str,
        description: str = "",
        start_location_id: str = "start",
    ) -> tuple[AuthoringWorldSummary, ValidationReport]:
        world_path = self._safe_new_world_path(world_id)
        world_path.mkdir(parents=True)
        files = self._initial_world_files(world_id, name, description, start_location_id)
        for file_name, data in files.items():
            (world_path / file_name).write_text(
                yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
        report = self.validate_world(world_id)
        return self.get_world_summary(world_id), report

    def _safe_world_path(self, world_id: str) -> Path:
        if not _is_safe_id(world_id):
            raise AuthoringError(f"Invalid world_id: {world_id}")
        root = self.worlds_root.resolve()
        path = (root / world_id).resolve()
        if root != path and root not in path.parents:
            raise AuthoringError("World path escapes worlds root")
        if not path.exists() or not path.is_dir():
            raise AuthoringError(f"World pack not found: {world_id}")
        return path

    def _safe_new_world_path(self, world_id: str) -> Path:
        if not _is_safe_id(world_id):
            raise AuthoringError(f"Invalid world_id: {world_id}")
        root = self.worlds_root.resolve()
        path = (root / world_id).resolve()
        if root != path and root not in path.parents:
            raise AuthoringError("World path escapes worlds root")
        if path.exists():
            raise AuthoringError(f"World pack already exists: {world_id}")
        return path

    def _safe_file_path(self, world_id: str, file_name: str) -> Path:
        if file_name not in ALLOWED_AUTHORING_FILES or Path(file_name).name != file_name:
            raise AuthoringError(f"File is not authoring-allowed: {file_name}")
        world_path = self._safe_world_path(world_id)
        path = (world_path / file_name).resolve()
        if world_path.resolve() != path.parent:
            raise AuthoringError("Content file path escapes world pack")
        return path

    def _read_manifest(self, path: Path) -> WorldManifest | None:
        if not path.exists():
            return None
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                return None
            return WorldManifest.model_validate(data)
        except (yaml.YAMLError, ValueError):
            return None

    def _parse_yaml(self, content: str, file_name: str) -> Any:
        try:
            data = yaml.safe_load(content) or {}
        except yaml.YAMLError as exc:
            raise AuthoringError(f"Invalid YAML in {file_name}: {exc}") from exc
        if not isinstance(data, dict):
            raise AuthoringError(f"Expected YAML mapping in {file_name}")
        return data

    def _initial_world_files(
        self,
        world_id: str,
        name: str,
        description: str,
        start_location_id: str,
    ) -> dict[str, dict[str, Any]]:
        files: dict[str, dict[str, Any]] = {
            "manifest.yaml": {
                "world_id": world_id,
                "name": name,
                "version": "0.1.0",
                "description": description,
                "start_location_id": start_location_id,
            },
            "locations.yaml": {
                "locations": [
                    {
                        "id": start_location_id,
                        "name": "Start",
                        "description": "A new local world begins here.",
                        "exits": {},
                    }
                ]
            },
        }
        for file_name, key in LIST_FILE_KEYS.items():
            files.setdefault(file_name, {key: []})
        return files


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)
