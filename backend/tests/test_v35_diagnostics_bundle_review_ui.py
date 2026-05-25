from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_diagnostics_bundle_review_ui_frontend_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    api_source = (ROOT / "frontend" / "src" / "api.ts").read_text(encoding="utf-8")

    for alternatives in [
        ("Diagnostics Bundle Review UI", "诊断包预览"),
        ("Diagnostics Preview", "诊断包预览"),
        ("Included sections", "包含内容", "included_sections"),
        ("Excluded sections", "默认排除内容", "excluded_sections"),
        ("app summary", "应用安全摘要", "app_summary"),
        ("project safe summary", "项目安全摘要", "project_safe_summary"),
        ("provider safe summary", "Provider 安全摘要", "provider_safe_summary"),
        ("quality summary", "质量检查摘要", "quality_summary"),
        ("module status", "模块状态", "module_status"),
        ("recent redacted errors", "近期脱敏错误", "recent_redacted_errors"),
        ("redacted logs", "脱敏日志", "redacted_logs"),
        (".env",),
        ("API key",),
        ("provider secrets",),
        ("raw env",),
        ("raw prompt/output",),
        ("hidden facts",),
        ("NPC secrets",),
        ("debug memory",),
        ("raw state_deltas",),
        ("mature/private",),
        ("database files",),
        ("Create Diagnostics Bundle", "创建本地诊断包"),
        ("I confirm debug bundle export", "我确认导出 Debug 包"),
        ("ENABLE_DEBUG_API",),
        ("No upload was performed", "不会上传", "没有上传"),
        ("buildDiagnosticsSafePayloadPreview",),
    ]:
        assert any(token in app_source for token in alternatives), alternatives

    assert "createDiagnosticsBundle" in api_source
    panel_source = app_source[
        app_source.index("function DiagnosticsBundlePanel") :
        app_source.index("function LocalConfigWizardPanel")
    ]
    assert "JSON.stringify(preview.safe_payload" not in panel_source
    assert "<pre>" not in panel_source
    assert "upload" in panel_source.lower()
    assert "confirmedDebug" in panel_source
