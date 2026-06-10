from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/physical_ai_package.py")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], check=False, text=True, capture_output=True)


def test_import_lerobot_maps_args_to_importer_request(monkeypatch, tmp_path: Path, capsys):
    from physical_ai_data import cli
    from physical_ai_data.importers import ImportResult

    class FakeLeRobotPackageImporter:
        source_format = "lerobot"

    importer_instances = []

    def fake_importer() -> FakeLeRobotPackageImporter:
        importer = FakeLeRobotPackageImporter()
        importer_instances.append(importer)
        return importer

    def fake_run_import(importer: FakeLeRobotPackageImporter, request):
        assert importer is importer_instances[0]
        assert request.source_format == "lerobot"
        assert request.source == {
            "repo_id": "lerobot/pusht",
            "episode_index": 2,
            "root": tmp_path / "lerobot-root",
        }
        assert request.output_dir == tmp_path / "pkg"
        assert request.options == {
            "profile": "aloha",
            "max_frames": 5,
            "camera": "wrist",
        }
        return ImportResult(
            package_root=tmp_path / "pkg",
            source_format="lerobot",
            source_id="lerobot/pusht#episode=2",
            frame_count=5,
        )

    monkeypatch.setattr(cli, "LeRobotPackageImporter", fake_importer)
    monkeypatch.setattr(cli, "run_import", fake_run_import)

    output_dir = tmp_path / "pkg"
    result = cli.main(
        [
            "import-lerobot",
            "--repo-id",
            "lerobot/pusht",
            "--episode-index",
            "2",
            "--output-dir",
            str(output_dir),
            "--root",
            str(tmp_path / "lerobot-root"),
            "--profile",
            "aloha",
            "--max-frames",
            "5",
            "--camera",
            "wrist",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Imported LeRobot episode to Physical AI Package" in captured.out
    assert str(output_dir) in captured.out


def test_import_lerobot_help_lists_options():
    result = _run(["import-lerobot", "--help"])

    assert result.returncode == 0
    assert "--repo-id" in result.stdout
    assert "--episode-index" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--root" in result.stdout
    assert "--max-frames" in result.stdout
    assert "--profile" in result.stdout
    assert "--camera" in result.stdout
    assert "LeRobot repository ID." in result.stdout
    assert "Output package directory." in result.stdout


def test_import_lerobot_rejects_non_positive_max_frames(tmp_path: Path, capsys):
    from physical_ai_data import cli

    result = cli.main(
        [
            "import-lerobot",
            "--repo-id",
            "lerobot/pusht",
            "--episode-index",
            "0",
            "--output-dir",
            str(tmp_path / "pkg"),
            "--max-frames",
            "0",
        ]
    )

    captured = capsys.readouterr()
    assert result != 0
    assert "max_frames must be positive" in captured.err
