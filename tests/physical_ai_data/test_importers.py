from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pytest

from physical_ai_data.csv_recording_importer import CsvRecordingPackageImporter
from physical_ai_data.importers import ImportRequest, ImportResult, run_import
from physical_ai_data.lerobot_adapter import LeRobotEpisode, LeRobotFrame, LeRobotPackageImporter
from physical_ai_data.schema import ValidationMessage, ValidationResult
from physical_ai_data.validation import validate_package


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


def _write_csv_recording_source(root: Path) -> Path:
    image = root / "images" / "front.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"fake png bytes")
    rows = [
        {
            "timestamp_s": "0.0",
            "phase": "observe",
            "image_path": "images/front.png",
            "metric_name": "object_confidence",
            "metric_value": "0.81",
            "event_type": "start",
            "event_severity": "info",
            "event_message": "Recording started",
            "label_type": "task_context",
            "label_value": "demo",
            "label_confidence": "1.0",
        },
        {
            "timestamp_s": "0.1",
            "phase": "grasp",
            "image_path": "",
            "metric_name": "grip_confidence",
            "metric_value": "0.73",
            "event_type": "grasp_attempt",
            "event_severity": "warning",
            "event_message": "Grip confidence needs review",
            "label_type": "quality",
            "label_value": "",
            "label_confidence": "",
        },
        {
            "timestamp_s": "0.2",
            "phase": "finish",
            "image_path": "",
            "metric_name": "",
            "metric_value": "",
            "event_type": "",
            "event_severity": "",
            "event_message": "",
            "label_type": "",
            "label_value": "",
            "label_confidence": "",
        },
    ]
    path = root / "frames.csv"
    root.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return root


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def test_csv_recording_importer_generates_valid_package(tmp_path: Path):
    source = _write_csv_recording_source(tmp_path / "source")
    request = ImportRequest(source_format="csv_recording", source={"root": source}, output_dir=tmp_path / "package")

    result = run_import(CsvRecordingPackageImporter(), request)

    validation = validate_package(result.package_root)
    assert validation.ok
    assert result.source_format == "csv_recording"
    assert result.source_id == str(source)
    assert result.frame_count == 3
    assert (result.package_root / "artifacts" / "images" / "frame_0000.png").exists()
    assert (result.package_root / "artifacts" / "source" / "csv_recording_frames.csv").exists()

    manifest = json.loads((result.package_root / "physical_ai_manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenario_type"] == "arm_pick_sort"
    assert manifest["source_dataset"]["format"] == "csv_recording"
    assert manifest["source_dataset"]["root"] == str(source)
    assert manifest["source_dataset"]["frames_csv_ref"] == "artifacts/source/csv_recording_frames.csv"
    assert manifest["source_dataset"]["frame_count"] == 3
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", manifest["source_dataset"]["converted_at"])

    frames = _read_csv_rows(result.package_root / "frames.csv")
    events = _read_csv_rows(result.package_root / "events.csv")
    labels = _read_csv_rows(result.package_root / "labels.csv")
    metrics = _read_csv_rows(result.package_root / "metrics.csv")

    assert [row["frame_id"] for row in frames] == ["frame_0000", "frame_0001", "frame_0002"]
    assert frames[0]["timeline"] == "sim_time"
    assert frames[0]["coordinate_frame_id"] == "robot_base"
    assert frames[0]["image_ref"] == "artifacts/images/frame_0000.png"
    assert frames[1]["image_ref"] == ""

    assert len(metrics) == 2
    assert [row["metric_id"] for row in metrics] == ["metric_0000", "metric_0001"]
    assert {row["metric_name"] for row in metrics} == {"object_confidence", "grip_confidence"}

    assert len(events) == 2
    assert events[0]["event_id"] == "event_0000"
    assert events[0]["severity"] == "info"
    assert events[0]["message"] == "Recording started"
    assert events[0]["related_frame_id"] == "frame_0000"
    assert events[1]["severity"] == "warning"
    assert events[1]["related_frame_id"] == "frame_0001"

    assert len(labels) == 2
    assert labels[0]["label_id"] == "label_0000"
    assert labels[0]["target_ref"] == "frame:frame_0000"
    assert labels[0]["confidence"] == "1.0"
    assert labels[1]["target_ref"] == "frame:frame_0001"
    assert labels[1]["value"] == ""
    assert labels[1]["confidence"] == "1.0"


def test_csv_recording_importer_rejects_source_format_mismatch(tmp_path: Path):
    request = ImportRequest(source_format="other", source={"root": tmp_path}, output_dir=tmp_path / "package")

    with pytest.raises(ValueError, match="CSV recording importer cannot handle other"):
        CsvRecordingPackageImporter().import_package(request)


def test_csv_recording_importer_rejects_missing_root(tmp_path: Path):
    request = ImportRequest(source_format="csv_recording", source={}, output_dir=tmp_path / "package")

    with pytest.raises(ValueError, match="source.root must be a path string or Path"):
        CsvRecordingPackageImporter().import_package(request)


def test_csv_recording_importer_rejects_missing_required_columns(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "frames.csv").write_text("timestamp_s,phase\n0.0,observe\n", encoding="utf-8")
    request = ImportRequest(source_format="csv_recording", source={"root": source}, output_dir=tmp_path / "package")

    with pytest.raises(ValueError, match="frames.csv missing required columns"):
        CsvRecordingPackageImporter().import_package(request)


@pytest.mark.parametrize("image_path", ["/tmp/frame.png", "../frame.png"])
def test_csv_recording_importer_rejects_absolute_or_parent_image_path(tmp_path: Path, image_path: str):
    source = _write_csv_recording_source(tmp_path / "source")
    rows = _read_csv_rows(source / "frames.csv")
    rows[0]["image_path"] = image_path
    _write_csv_rows(source / "frames.csv", list(rows[0].keys()), rows)
    request = ImportRequest(source_format="csv_recording", source={"root": source}, output_dir=tmp_path / "package")

    with pytest.raises(ValueError, match="image_path must be relative to source.root"):
        CsvRecordingPackageImporter().import_package(request)


def test_csv_recording_importer_copy_images_false_leaves_image_refs_empty(tmp_path: Path):
    source = _write_csv_recording_source(tmp_path / "source")
    request = ImportRequest(
        source_format="csv_recording",
        source={"root": source},
        output_dir=tmp_path / "package",
        options={"copy_images": False},
    )

    result = run_import(CsvRecordingPackageImporter(), request)

    validation = validate_package(result.package_root)
    frames = _read_csv_rows(result.package_root / "frames.csv")
    assert validation.ok
    assert {row["image_ref"] for row in frames} == {""}
    assert not list((result.package_root / "artifacts" / "images").glob("*.png"))


def test_csv_recording_importer_defaults_optional_event_and_label_fields(tmp_path: Path):
    source = _write_csv_recording_source(tmp_path / "source")
    rows = _read_csv_rows(source / "frames.csv")
    rows[0]["event_severity"] = ""
    rows[0]["event_message"] = ""
    rows[0]["label_confidence"] = ""
    _write_csv_rows(source / "frames.csv", list(rows[0].keys()), rows)
    request = ImportRequest(source_format="csv_recording", source={"root": source}, output_dir=tmp_path / "package")

    result = run_import(CsvRecordingPackageImporter(), request)

    events = _read_csv_rows(result.package_root / "events.csv")
    labels = _read_csv_rows(result.package_root / "labels.csv")
    assert events[0]["severity"] == "info"
    assert events[0]["message"] == ""
    assert labels[0]["confidence"] == "1.0"
    assert labels[0]["target_ref"] == "frame:frame_0000"
