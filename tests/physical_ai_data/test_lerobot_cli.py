from __future__ import annotations

import subprocess
from pathlib import Path


SCRIPT = Path("scripts/physical_ai_package.py")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", str(SCRIPT), *args], check=False, text=True, capture_output=True)


def test_import_lerobot_calls_loader_and_writes_package(monkeypatch, tmp_path: Path, capsys):
    from physical_ai_data import cli
    from physical_ai_data.lerobot_adapter import LeRobotEpisode, LeRobotFrame

    front_image = tmp_path / "front.png"
    front_image.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01"
        b"\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    episode = LeRobotEpisode(
        repo_id="lerobot/pusht",
        episode_index=0,
        fps=10.0,
        frames=[
            LeRobotFrame(
                frame_index=0,
                timestamp_s=0.0,
                state=[0.0, 1.0],
                action=[0.5, 0.25],
                images={"front": front_image},
            )
        ],
        task_name="PushT",
        profile="pusht",
        root=None,
        features={"observation.state": {"dtype": "float32", "shape": [2]}},
        stats={"observation.state": {"mean": [0.0, 0.0]}},
        episode_metadata={"episode_index": 0},
        task_metadata={"task": "PushT"},
    )

    def fake_load_lerobot_episode(**kwargs):
        assert kwargs["repo_id"] == "lerobot/pusht"
        assert kwargs["episode_index"] == 0
        assert kwargs["root"] is None
        assert kwargs["profile"] == "auto"
        assert kwargs["max_frames"] == 1
        assert kwargs["camera"] is None
        return episode

    monkeypatch.setattr("physical_ai_data.lerobot_loader.load_lerobot_episode", fake_load_lerobot_episode)

    output_dir = tmp_path / "pkg"
    result = cli.main(
        [
            "import-lerobot",
            "--repo-id",
            "lerobot/pusht",
            "--episode-index",
            "0",
            "--output-dir",
            str(output_dir),
            "--max-frames",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Physical AI Package" in captured.out
    assert (output_dir / "physical_ai_manifest.json").exists()


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
