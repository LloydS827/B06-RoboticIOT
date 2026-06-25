from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OptionalDependencyStatus:
    name: str
    installed: bool
    import_error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "installed": self.installed,
            "import_error": self.import_error,
        }


@dataclass(frozen=True)
class SdkEnvironmentReport:
    package_version: str
    package_file: str | None
    package_path_exists: bool
    python_executable: str
    cwd: str
    console_entrypoint: str | None
    console_entrypoint_exists: bool
    optional_dependencies: list[OptionalDependencyStatus]
    warnings: list[str]
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "package_version": self.package_version,
            "package_file": self.package_file,
            "package_path_exists": self.package_path_exists,
            "python_executable": self.python_executable,
            "cwd": self.cwd,
            "console_entrypoint": self.console_entrypoint,
            "console_entrypoint_exists": self.console_entrypoint_exists,
            "optional_dependencies": {
                dependency.name: dependency.to_dict() for dependency in self.optional_dependencies
            },
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


def inspect_sdk_environment() -> SdkEnvironmentReport:
    import physical_ai_data

    warnings: list[str] = []
    errors: list[str] = []
    cwd = Path.cwd()
    current_tree_root = _find_current_tree_root(cwd)

    package_file = getattr(physical_ai_data, "__file__", None)
    package_path_exists = bool(package_file and Path(package_file).exists())
    if package_file is None:
        errors.append("physical_ai_data.__file__ is missing")
    elif not package_path_exists:
        errors.append(f"physical_ai_data.__file__ path does not exist: {package_file}")
    elif current_tree_root is not None and not _is_relative_to(Path(package_file), current_tree_root):
        errors.append(
            "physical_ai_data.__file__ is outside the current working tree: "
            f"{package_file}"
        )

    console_entrypoint = shutil.which("physical-ai-package")
    console_entrypoint_exists = bool(console_entrypoint and Path(console_entrypoint).exists())
    if console_entrypoint is None:
        warnings.append("physical-ai-package console entrypoint is not on PATH")
    elif not console_entrypoint_exists:
        warnings.append(f"physical-ai-package console entrypoint path does not exist: {console_entrypoint}")

    optional_dependencies = [_inspect_optional_dependency(name) for name in ("rerun", "lerobot")]
    for dependency in optional_dependencies:
        if not dependency.installed:
            warnings.append(f"optional dependency {dependency.name} is not installed")

    return SdkEnvironmentReport(
        package_version=getattr(physical_ai_data, "__version__", "unknown"),
        package_file=package_file,
        package_path_exists=package_path_exists,
        python_executable=sys.executable,
        cwd=str(cwd),
        console_entrypoint=console_entrypoint,
        console_entrypoint_exists=console_entrypoint_exists,
        optional_dependencies=optional_dependencies,
        warnings=warnings,
        errors=errors,
    )


def _inspect_optional_dependency(name: str) -> OptionalDependencyStatus:
    try:
        installed = importlib.util.find_spec(name) is not None
    except Exception as exc:
        return OptionalDependencyStatus(name=name, installed=False, import_error=str(exc))
    return OptionalDependencyStatus(name=name, installed=installed)


def _find_current_tree_root(cwd: Path) -> Path | None:
    for candidate in (cwd, *cwd.parents):
        if (candidate / "src" / "physical_ai_data").is_dir():
            return candidate
    return None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True
