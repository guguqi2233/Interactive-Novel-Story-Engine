from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from app.engine.gameplay_module_loader import GameplayModuleLoader
from app.platform.package_v2 import PackageV2Importer


class LocalModuleBrowserItem(BaseModel):
    module_id: str
    name: str
    version: str
    status: str = "discovered"
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class LocalScriptPackageItem(BaseModel):
    package_id: str
    package_type: str = "script"
    version: str = "unknown"
    status: str = "discovered"
    warnings: list[str] = Field(default_factory=list)


class LocalModuleBrowserService:
    def __init__(self, modules_root: str | Path = "gameplay_modules") -> None:
        self.loader = GameplayModuleLoader(modules_root)

    def list_items(self) -> list[LocalModuleBrowserItem]:
        items: list[LocalModuleBrowserItem] = []
        for info in self.loader.discover_modules():
            items.append(
                LocalModuleBrowserItem(
                    module_id=info.manifest.id,
                    name=info.manifest.name,
                    version=info.manifest.version,
                    dependencies=info.manifest.dependencies,
                    conflicts=info.manifest.conflicts,
                )
            )
        return items


class LocalScriptPackageBrowserService:
    def __init__(self, packages_root: str | Path = "packages") -> None:
        self.packages_root = Path(packages_root)
        self.importer = PackageV2Importer()

    def list_items(self) -> list[LocalScriptPackageItem]:
        if not self.packages_root.exists():
            return []
        return [
            LocalScriptPackageItem(package_id=path.stem, status="available")
            for path in sorted(self.packages_root.glob("*.zip"), key=lambda item: item.name)
        ]

    def import_dry_run(self, archive_base64: str):
        return self.importer.dry_run(archive_base64)

