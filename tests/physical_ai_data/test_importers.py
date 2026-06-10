from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pytest

from physical_ai_data.importers import ImportRequest, ImportResult, run_import
from physical_ai_data.lerobot_adapter import LeRobotEpisode, LeRobotFrame, LeRobotPackageImporter
from physical_ai_data.schema import ValidationMessage, ValidationResult


@dataclass
class _FakeImporter:
    source_format: str = "fake"

    def import_package(self, request: ImportRequest) -> ImportResult:
        return ImportResult(
            package_root=request.output_dir,
            source_format=self.source_format,
            source_id="fake-source",
            frame_count=3,
        )


def _source_image(tmp_path: Path) -> Path:
    image_path = tmp_path / "source_images" / "front_0000.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"fake image bytes")
    return image_path


def _episode(tmp_path: Path, *, closed: list[bool] | None = None) -> LeRobotEpisode:
    class _ClosableEpisode(LeRobotEpisode):
        def close(self) -> None:
            if closed is not None:
                closed.append(True)
            super().close()

    return _ClosableEpisode(
        repo_id="lerobot/pusht",
        episode_index=7,
        fps=10.0,
        task_name="PushT",
        profile="pusht",
        root=tmp_path / "dataset_root",
        features={"observation.image": {"dtype": "image"}},
        stats={},
        episode_metadata={"episode_index": 7},
        task_metadata={"task": "PushT"},
        frames=[
            LeRobotFrame(
                frame_index=0,
                timestamp_s=0.0,
                images={"front": _source_image(tmp_path)},
                state=[0.1, 0.2],
                action=[0.3],
            )
        ],
    )


def test_run_import_returns_fake_importer_result(tmp_path: Path):
    request = ImportRequest(source_format="fake", source={}, output_dir=tmp_path / "package")

    result = run_import(_FakeImporter(), request)

    assert result == ImportResult(
        package_root=tmp_path / "package",
        source_format="fake",
        source_id="fake-source",
        frame_count=3,
    )


def test_run_import_rejects_source_format_mismatch(tmp_path: Path):
    request = ImportRequest(source_format="other", source={}, output_dir=tmp_path / "package")

    with pytest.raises(ValueError, match="Importer source_format fake cannot handle other"):
        run_import(_FakeImporter(), request)


def test_lerobot_package_importer_maps_request_to_loader_and_returns_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import physical_ai_data.lerobot_loader as lerobot_loader

    calls: list[Mapping[str, object]] = []

    def fake_loader(
        *,
        repo_id: str,
        episode_index: int,
        root: str | Path | None = None,
        profile: str = "auto",
        max_frames: int | None = None,
        camera: str | None = None,
    ) -> LeRobotEpisode:
        calls.append(
            {
                "repo_id": repo_id,
                "episode_index": episode_index,
                "root": root,
                "profile": profile,
                "max_frames": max_frames,
                "camera": camera,
            }
        )
        return _episode(tmp_path)

    monkeypatch.setattr(lerobot_loader, "load_lerobot_episode", fake_loader)
    request = ImportRequest(
        source_format="lerobot",
        source={
            "repo_id": "lerobot/pusht",
            "episode_index": 7,
            "root": tmp_path / "dataset_root",
        },
        output_dir=tmp_path / "package",
        options={"profile": "pusht", "max_frames": 1, "camera": "front"},
    )

    result = run_import(LeRobotPackageImporter(), request)

    assert calls == [
        {
            "repo_id": "lerobot/pusht",
            "episode_index": 7,
            "root": tmp_path / "dataset_root",
            "profile": "pusht",
            "max_frames": 1,
            "camera": "front",
        }
    ]
    manifest = json.loads((tmp_path / "package" / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_dataset"]["format"] == "lerobot"
    assert result == ImportResult(
        package_root=tmp_path / "package",
        source_format="lerobot",
        source_id="lerobot/pusht#episode=7",
        frame_count=1,
    )


def test_lerobot_package_importer_closes_loaded_episode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import physical_ai_data.lerobot_loader as lerobot_loader

    closed: list[bool] = []

    def fake_loader(
        repo_id: str,
        episode_index: int,
        root: str | Path | None = None,
        profile: str = "auto",
        max_frames: int | None = None,
        camera: str | None = None,
    ) -> LeRobotEpisode:
        return _episode(tmp_path, closed=closed)

    monkeypatch.setattr(lerobot_loader, "load_lerobot_episode", fake_loader)
    request = ImportRequest(
        source_format="lerobot",
        source={"repo_id": "lerobot/pusht", "episode_index": 7},
        output_dir=tmp_path / "package",
    )

    LeRobotPackageImporter().import_package(request)

    assert closed == [True]


def test_lerobot_package_importer_rejects_direct_source_format_mismatch_before_loading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import physical_ai_data.lerobot_loader as lerobot_loader

    def fake_loader(
        repo_id: str,
        episode_index: int,
        root: str | Path | None = None,
        profile: str = "auto",
        max_frames: int | None = None,
        camera: str | None = None,
    ) -> LeRobotEpisode:
        raise AssertionError("loader should not be called")

    monkeypatch.setattr(lerobot_loader, "load_lerobot_episode", fake_loader)
    request = ImportRequest(
        source_format="other",
        source={"repo_id": "lerobot/pusht", "episode_index": 7},
        output_dir=tmp_path / "package",
    )

    with pytest.raises(ValueError, match="LeRobot importer cannot handle other"):
        LeRobotPackageImporter().import_package(request)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ({"episode_index": 7}, "source.repo_id must be a string"),
        ({"repo_id": "lerobot/pusht", "episode_index": "7"}, "source.episode_index must be an integer"),
        (
            {"repo_id": "lerobot/pusht", "episode_index": 7, "root": object()},
            "source.root must be a path string or Path",
        ),
    ],
)
def test_lerobot_package_importer_rejects_invalid_required_source_fields(
    tmp_path: Path,
    source: Mapping[str, object],
    message: str,
):
    request = ImportRequest(source_format="lerobot", source=source, output_dir=tmp_path / "package")

    with pytest.raises(ValueError, match=message):
        LeRobotPackageImporter().import_package(request)


def test_lerobot_package_importer_reports_validation_error_codes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import physical_ai_data.lerobot_loader as lerobot_loader
    import physical_ai_data.lerobot_adapter as lerobot_adapter

    def fake_loader(
        repo_id: str,
        episode_index: int,
        root: str | Path | None = None,
        profile: str = "auto",
        max_frames: int | None = None,
        camera: str | None = None,
    ) -> LeRobotEpisode:
        return _episode(tmp_path)

    def fake_validate_package(package_root: str | Path) -> ValidationResult:
        return ValidationResult(
            errors=[ValidationMessage("missing_manifest", "Missing manifest", str(package_root))],
            summary={"frame_count": 0},
        )

    monkeypatch.setattr(lerobot_loader, "load_lerobot_episode", fake_loader)
    monkeypatch.setattr(lerobot_adapter, "validate_package", fake_validate_package)
    request = ImportRequest(
        source_format="lerobot",
        source={"repo_id": "lerobot/pusht", "episode_index": 7},
        output_dir=tmp_path / "package",
    )

    with pytest.raises(ValueError, match="missing_manifest"):
        LeRobotPackageImporter().import_package(request)


def test_lerobot_package_importer_returns_validation_warning_code_and_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import physical_ai_data.lerobot_loader as lerobot_loader
    import physical_ai_data.lerobot_adapter as lerobot_adapter

    def fake_loader(
        repo_id: str,
        episode_index: int,
        root: str | Path | None = None,
        profile: str = "auto",
        max_frames: int | None = None,
        camera: str | None = None,
    ) -> LeRobotEpisode:
        return _episode(tmp_path)

    def fake_validate_package(package_root: str | Path) -> ValidationResult:
        return ValidationResult(
            warnings=[
                ValidationMessage(
                    "recommended_artifact_dir_missing",
                    "Missing artifacts/images",
                    str(package_root),
                )
            ],
            summary={"frame_count": 1},
        )

    monkeypatch.setattr(lerobot_loader, "load_lerobot_episode", fake_loader)
    monkeypatch.setattr(lerobot_adapter, "validate_package", fake_validate_package)
    request = ImportRequest(
        source_format="lerobot",
        source={"repo_id": "lerobot/pusht", "episode_index": 7},
        output_dir=tmp_path / "package",
    )

    result = LeRobotPackageImporter().import_package(request)

    assert result.warnings == ["recommended_artifact_dir_missing: Missing artifacts/images"]
