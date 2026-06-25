from __future__ import annotations

from pathlib import Path

from physical_ai_data.environment import inspect_sdk_environment


def test_inspect_sdk_environment_reports_current_package_path():
    report = inspect_sdk_environment()
    payload = report.to_dict()

    assert payload["package_version"] == "0.1.0"
    assert Path(payload["package_file"]).exists()
    assert payload["package_path_exists"] is True
    assert payload["python_executable"]
    assert "optional_dependencies" in payload
    assert "rerun" in payload["optional_dependencies"]
    assert "lerobot" in payload["optional_dependencies"]
    assert payload["ok"] is True


def test_inspect_sdk_environment_errors_when_package_file_is_missing(monkeypatch):
    import physical_ai_data
    import physical_ai_data.environment as environment

    monkeypatch.setattr(physical_ai_data, "__file__", "/tmp/b06_missing_sdk/__init__.py")

    report = environment.inspect_sdk_environment()

    assert report.ok is False
    assert report.to_dict()["errors"]


def test_inspect_sdk_environment_errors_when_package_file_is_outside_current_repo(
    monkeypatch,
    tmp_path: Path,
):
    import physical_ai_data
    import physical_ai_data.environment as environment

    stale_package = tmp_path / "stale-worktree" / "src" / "physical_ai_data" / "__init__.py"
    stale_package.parent.mkdir(parents=True)
    stale_package.write_text('"""stale package"""', encoding="utf-8")

    monkeypatch.setattr(physical_ai_data, "__file__", str(stale_package))

    report = environment.inspect_sdk_environment()

    assert report.ok is False
    assert any("current working tree" in error for error in report.errors)


def test_inspect_sdk_environment_warns_when_console_entrypoint_is_missing(monkeypatch):
    import physical_ai_data.environment as environment

    monkeypatch.setattr(environment.shutil, "which", lambda name: None)

    report = environment.inspect_sdk_environment()

    assert report.ok is True
    assert any("physical-ai-package" in warning for warning in report.warnings)


def test_inspect_sdk_environment_warns_when_optional_dependencies_are_missing(monkeypatch):
    import physical_ai_data.environment as environment

    real_find_spec = environment.importlib.util.find_spec

    def fake_find_spec(name):
        if name in {"rerun", "lerobot"}:
            return None
        return real_find_spec(name)

    monkeypatch.setattr(environment.importlib.util, "find_spec", fake_find_spec)

    report = environment.inspect_sdk_environment()
    payload = report.to_dict()

    assert report.ok is True
    assert payload["optional_dependencies"]["rerun"]["installed"] is False
    assert payload["optional_dependencies"]["lerobot"]["installed"] is False
    assert any("rerun" in warning for warning in report.warnings)
    assert any("lerobot" in warning for warning in report.warnings)
