from __future__ import annotations

import base64
import json
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.platform.package_v2 import PackageV2Importer
from app.platform.save_migration_v2 import plan_save_migration_v2


def test_v1_package_enters_v2_legacy_warning_path() -> None:
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as archive:
        archive.writestr("local_package_manifest.json", json.dumps({"package_id": "legacy", "package_type": "world", "contract_version": "1.8"}))
    result = PackageV2Importer().dry_run(base64.b64encode(buf.getvalue()).decode("ascii"))
    assert result.report.ok
    assert result.report.legacy_v1_detected
    assert result.report.warnings


def test_campaignless_v1_save_can_plan_default_v2_migration() -> None:
    plan = plan_save_migration_v2("1")
    assert plan.can_migrate
    assert plan.target_version == "2"

