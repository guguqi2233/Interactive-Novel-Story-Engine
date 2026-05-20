from pathlib import Path

from app.config import Settings
from app.desktop.studio_policy import (
    BackupBundle,
    CrashReport,
    DesktopStudioPolicy,
    LocalLog,
)


def test_safe_config_summary_does_not_contain_api_key() -> None:
    policy = DesktopStudioPolicy()
    settings = Settings(
        database_url="sqlite:///C:/private/world_engine.db",
        llm_provider="openai",
        llm_api_key="sk-test-secret-that-must-not-appear",
    )

    summary = policy.build_safe_config_summary(settings)
    serialized = summary.model_dump_json()

    assert summary.api_key_configured is True
    assert summary.database_path_hint == "sqlite local file: world_engine.db"
    assert "sk-test-secret-that-must-not-appear" not in serialized
    assert "C:/private" not in serialized
    assert "DATABASE_URL" not in serialized
    assert "LLM_API_KEY" not in serialized


def test_backup_bundle_rejects_env_and_api_key_content() -> None:
    policy = DesktopStudioPolicy()
    decision = policy.validate_backup_bundle(
        BackupBundle(
            file_paths=[
                "worlds/demo/manifest.yaml",
                ".env",
                "logs/backend.log",
                "backups/old.zip",
                "crash-reports/report.json",
                "desktop_build/app.bin",
                "release/app.exe",
                "scripts/run.ps1",
            ],
            content_preview="LLM_API_KEY=sk-test-secret-that-must-not-appear",
        )
    )

    assert decision.allowed is False
    assert "backup_contains_forbidden_file:.env" in decision.blockers
    assert "backup_contains_forbidden_suffix:logs/backend.log" in decision.blockers
    assert "backup_contains_forbidden_directory:backups/old.zip" in decision.blockers
    assert "backup_contains_forbidden_directory:crash-reports/report.json" in decision.blockers
    assert "backup_contains_forbidden_directory:desktop_build/app.bin" in decision.blockers
    assert "backup_contains_forbidden_directory:release/app.exe" in decision.blockers
    assert "backup_contains_executable_file:release/app.exe" in decision.blockers
    assert "backup_contains_executable_file:scripts/run.ps1" in decision.blockers
    assert "backup_contains_secret_preview" in decision.blockers


def test_crash_report_normal_view_does_not_include_raw_env() -> None:
    policy = DesktopStudioPolicy()
    safe_report = policy.sanitize_crash_report(
        CrashReport(
            title="backend failed",
            message="Provider failed with LLM_API_KEY=sk-test-secret-that-must-not-appear",
            raw_env={"LLM_API_KEY": "sk-test-secret-that-must-not-appear"},
            stack_trace="RuntimeError: sk-test-secret-that-must-not-appear",
        )
    )

    serialized = str(safe_report)
    assert safe_report["raw_env_included"] is False
    assert "sk-test-secret-that-must-not-appear" not in serialized
    assert "LLM_API_KEY" not in serialized


def test_frontend_config_rejects_secrets() -> None:
    policy = DesktopStudioPolicy()

    safe = policy.validate_frontend_config({"VITE_API_BASE_URL": "http://127.0.0.1:8000"})
    unsafe = policy.validate_frontend_config(
        {
            "VITE_API_BASE_URL": "http://127.0.0.1:8000",
            "VITE_LLM_API_KEY": "sk-test-secret-that-must-not-appear",
        }
    )

    assert safe.allowed is True
    assert unsafe.allowed is False
    assert "frontend_secret_env:VITE_LLM_API_KEY" in unsafe.blockers


def test_log_viewer_redacts_secrets_by_default() -> None:
    policy = DesktopStudioPolicy()
    redacted = policy.redact_log(
        LocalLog(
            path="logs/desktop-backend.err.log",
            text="OpenAI failed with OPENAI_API_KEY=sk-test-secret-that-must-not-appear",
        )
    )

    assert "sk-test-secret-that-must-not-appear" not in redacted.text
    assert "[redacted-secret]" in redacted.text


def test_desktop_scripts_do_not_hardcode_api_keys() -> None:
    policy = DesktopStudioPolicy()
    repo_root = Path(__file__).resolve().parents[2]
    scripts = [
        repo_root / "scripts" / "start_local_studio.ps1",
        repo_root / "scripts" / "start_local_studio.sh",
    ]

    for script in scripts:
        if not script.exists():
            continue
        decision = policy.validate_launcher_script(script.read_text(encoding="utf-8"))
        assert decision.allowed is True, f"{script}: {decision.blockers}"


def test_desktop_launcher_scripts_have_help_and_safety_language() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    scripts = {
        "powershell": repo_root / "scripts" / "start_local_studio.ps1",
        "shell": repo_root / "scripts" / "start_local_studio.sh",
    }

    ps1 = scripts["powershell"].read_text(encoding="utf-8")
    sh = scripts["shell"].read_text(encoding="utf-8")

    assert "-Help" in ps1
    assert "Show-Help" in ps1
    assert "--help" in sh
    assert "show_help" in sh
    for script_text in (ps1, sh):
        assert "Python 3.11+" in script_text
        assert "VITE_API_BASE_URL" in script_text
        assert "State safety" in script_text
        assert "LLM_API_KEY is not read" in script_text
        assert "GameState" in script_text
        assert "sk-" not in script_text


def test_gitignore_excludes_launcher_logs_and_desktop_outputs() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

    for expected in [
        ".env",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "logs/",
        "crash-reports/",
        "backups/",
        "cache/",
        "caches/",
        "frontend/dist/",
        "desktop-dist/",
        "desktop_build/",
        "desktop-build/",
        "desktop-release/",
        "electron-dist/",
        "tauri-dist/",
        "release/",
        "installers/",
    ]:
        assert expected in gitignore


def test_desktop_packaging_doc_has_safety_checklist() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    doc = (repo_root / "docs" / "DESKTOP_PACKAGING.md").read_text(encoding="utf-8")

    for expected in [
        "Packaging Safety Checklist",
        "python -m pytest",
        "npm.cmd run build",
        "git ls-files",
        ".env",
        "API keys",
        "frontend/dist",
        "desktop-dist",
        "desktop_build",
        "crash-reports",
        "backups",
        "No desktop workflow calls a real LLM provider",
    ]:
        assert expected in doc
