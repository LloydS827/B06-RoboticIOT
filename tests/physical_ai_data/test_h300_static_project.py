from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from physical_ai_data.h300_static_project import inspect_h300_static_project


def create_h300_static_project_fixture(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "campcd_json").mkdir()
    (root / "project_20260101_010101_image").mkdir()
    (root / "project_20260101_010101_point_cloud").mkdir()
    (root / "point_cloud").mkdir()
    (root / "weld_seam").mkdir()
    (root / "20260101_010101_weld_config").mkdir()
    (root / "20260101_010101_lua_script").mkdir()
    (root / "misc").mkdir()

    project_payload = {
        "info": {
            "projectName": "project_20260101_010101",
            "isTemplate": True,
            "workpieceSeamType": "plate",
            "author": "Operator_Wang",
            "dataRoot": "C:/SmartWeldData/project_20260101_010101",
        },
        "calibration": {
            "cameraToRobot": "present",
            "tcp": {"x": 1, "y": 2, "z": 3},
        },
        "camera": {"model": "synthetic", "server": "192.168.31.88", "port": 18801},
        "photoPoses": [{"id": "pose-1"}],
        "pathPlan": [{"id": "path-1"}, {"id": "path-2"}],
        "extractPathPlan": [{"id": "extract-1"}, {"id": "extract-2"}],
        "processes": [{"name": "vision_model_hint"}],
        "robot": {"controller": "ABB"},
        "runtime": {"program": "22222"},
    }
    _write_json(root / "campcd_json" / "project_20260101_010101.json", project_payload)

    campcd_payload = {
        "pcdWithCam": [
            {
                "image": "C:/SmartWeldData/project_20260101_010101_image/project_20260101_010101_part_0.jpg",
                "pcd": "C:/SmartWeldData/project_20260101_010101_point_cloud/project_20260101_010101_part_0.pcd",
                "pose": {"x": 1, "y": 2, "z": 3},
                "roi": {"enabled": True, "x": 10, "y": 20, "w": 30, "h": 40},
            }
        ]
    }
    _write_json(root / "campcd_json" / "project_20260101_010101_campcd.json", campcd_payload)

    Image.new("RGB", (17, 11), color=(10, 20, 30)).save(
        root / "project_20260101_010101_image" / "project_20260101_010101_part_0.jpg"
    )

    pcd_text = "\n".join(
        [
            "# .PCD v0.7",
            "VERSION 0.7",
            "FIELDS x y z",
            "SIZE 4 4 4",
            "TYPE F F F",
            "COUNT 1 1 1",
            "WIDTH 3",
            "HEIGHT 1",
            "VIEWPOINT 0 0 0 1 0 0 0",
            "POINTS 3",
            "DATA ascii",
            "9.876 8.765 7.654",
            "6.543 5.432 4.321",
            "3.210 2.109 1.098",
            "",
        ]
    )
    (root / "project_20260101_010101_point_cloud" / "project_20260101_010101_part_0.pcd").write_text(
        pcd_text,
        encoding="utf-8",
    )
    (root / "point_cloud" / "project_20260101_010101.txt").write_text(
        "123.456 234.567 345.678 0.5\n223.456 334.567 445.678 0.6\n",
        encoding="utf-8",
    )

    recipe_payload = {
        "operator": "Operator_Wang",
        "weld_seams": [
            {
                "id": "seam-1",
                "type": "fillet",
                "orientation": "left",
                "weld_type": "arc",
                "segments": [{"id": 1}, {"id": 2}],
                "measured_widths": [3.2, 3.3],
            },
            {
                "id": "seam-2",
                "type": "butt",
                "orientation": "right",
                "weld_type": "arc",
                "segments": [{"id": 1}],
                "measured_widths": [2.8],
            },
        ],
    }
    _write_json(root / "weld_seam" / "recipe2_project_20260101_010101.json", recipe_payload)

    flow_payload = {
        "server": "192.168.31.88",
        "port": 18801,
        "flow": [
            {"type": "load_project", "program": "22222"},
            {"type": "run_lua", "path": "C:/SmartWeldData/22222.lua"},
        ],
    }
    _write_json(root / "20260101_010101_weld_config" / "22222_flow.json", flow_payload)

    lua_text = """
    CONST robtarget pStart := [[1,2,3],[1,0,0,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST jointtarget jHome := [[0,0,0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST seamdata s1 := [1,1,1];
    CONST welddata w1 := [1,2,3];
    CONST weavedata weave1 := [1,2,3];
    CONST multipassdata mp1 := [1,2,3];
    MoveAbsJ jHome,v100,z50,tool0;
    MoveL pStart,v100,z10,tool0;
    ArcMPL pStart,v100,seam1,weld1,zone1,tool0;
    Stop;
    ! Operator_Wang C:/SmartWeldData 192.168.31.88 22222 project_20260101_010101
    """
    (root / "20260101_010101_lua_script" / "22222.lua").write_text(lua_text, encoding="utf-8")
    (root / "misc" / "Operator_Wang_notes.txt").write_text("review notes\n", encoding="utf-8")
    _write_json(root / "misc" / "client_alpha_config.json", {"enabled": True})
    (root / "misc" / "notes.client_alpha_secret").write_text("review notes\n", encoding="utf-8")

    return root


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_inspect_h300_static_project_summarizes_fixture_without_raw_values(tmp_path: Path):
    project = create_h300_static_project_fixture(tmp_path / "project")

    report = inspect_h300_static_project(project)
    payload = report.to_dict()

    assert payload["recognized"] is True
    assert payload["root_label"] == "<local-project>"
    assert payload["summary"]["image_count"] == 1
    assert payload["summary"]["point_cloud_count"] == 1
    assert payload["summary"]["text_point_cloud_count"] == 1
    assert payload["summary"]["weld_seam_count"] == 2
    assert payload["summary"]["path_plan_count"] == 2
    assert payload["summary"]["lua_arc_mpl_count"] == 1
    assert payload["project_info"]["has_project_name"] is True

    serialized = json.dumps(payload, sort_keys=True)
    assert "Operator_Wang" not in serialized
    assert "Operator_Wang_notes" not in serialized
    assert "client_alpha_config" not in serialized
    assert "client_alpha_secret" not in serialized
    assert ".client_alpha_secret" not in serialized
    assert "client_alpha" not in serialized
    assert "20260101" not in serialized
    assert "010101" not in serialized
    assert "22222" not in serialized
    assert "project_20260101_010101" not in serialized
    assert str(project) not in serialized
    assert str(tmp_path) not in serialized
    assert "C:/SmartWeldData" not in serialized
    assert "192.168" not in serialized
    assert "123.456" not in serialized
    assert "ArcMPL pStart" not in serialized
    assert ".txt" in serialized
    assert ".json" in serialized


def test_inspect_h300_static_project_handles_corrupt_image_and_adversarial_keys(tmp_path: Path):
    project = create_h300_static_project_fixture(tmp_path / "project")
    project_json_path = project / "campcd_json" / "project_20260101_010101.json"
    project_payload = json.loads(project_json_path.read_text(encoding="utf-8"))
    project_payload["client_alpha_secret"] = "present"
    project_payload["operator_Operator_Wang"] = "present"
    _write_json(project_json_path, project_payload)
    corrupt_image_name = "client_alpha_secret_broken.jpg"
    (project / "project_20260101_010101_image" / corrupt_image_name).write_bytes(b"not an image")

    payload = inspect_h300_static_project(project).to_dict()

    assert payload["summary"]["image_count"] == 1
    serialized = json.dumps(payload, sort_keys=True)
    assert "client_alpha_secret" not in serialized
    assert "client_alpha" not in serialized
    assert "operator_Operator_Wang" not in serialized
    assert "Operator_Wang" not in serialized
    assert corrupt_image_name not in serialized


def test_inspect_h300_static_project_redacts_adversarial_label_values(tmp_path: Path):
    project = create_h300_static_project_fixture(tmp_path / "project")

    project_json_path = project / "campcd_json" / "project_20260101_010101.json"
    project_payload = json.loads(project_json_path.read_text(encoding="utf-8"))
    project_payload["info"]["workpieceSeamType"] = "client_alpha_secret"
    _write_json(project_json_path, project_payload)

    recipe_path = project / "weld_seam" / "recipe2_project_20260101_010101.json"
    recipe_payload = json.loads(recipe_path.read_text(encoding="utf-8"))
    recipe_payload["weld_seams"][0]["type"] = "client_alpha_secret"
    recipe_payload["weld_seams"][0]["orientation"] = "operator_Operator_Wang"
    recipe_payload["weld_seams"][0]["weld_type"] = "client_alpha_secret"
    recipe_payload["weld_seams"][1]["type"] = "Fillet"
    recipe_payload["weld_seams"][1]["orientation"] = "vertical"
    _write_json(recipe_path, recipe_payload)

    flow_path = project / "20260101_010101_weld_config" / "22222_flow.json"
    flow_payload = json.loads(flow_path.read_text(encoding="utf-8"))
    flow_payload["flow"].append({"type": "operator_Operator_Wang"})
    _write_json(flow_path, flow_payload)

    pcd_path = project / "project_20260101_010101_point_cloud" / "project_20260101_010101_part_0.pcd"
    pcd_text = pcd_path.read_text(encoding="utf-8")
    pcd_text = pcd_text.replace("FIELDS x y z", "FIELDS x y z client_alpha_secret")
    pcd_path.write_text(pcd_text, encoding="utf-8")

    payload = inspect_h300_static_project(project).to_dict()

    assert payload["project_info"]["workpiece_seam_type"] == "<redacted>"
    assert payload["point_clouds"][0]["fields"] == ["x", "y", "z", "<redacted>"]
    assert payload["weld_seams"]["type_distribution"] == {"<redacted>": 1, "fillet": 1}
    assert payload["weld_seams"]["orientation_distribution"] == {"<redacted>": 1, "vertical": 1}
    assert payload["weld_seams"]["weld_type_distribution"] == {"<redacted>": 1, "arc": 1}
    assert payload["flow_config"]["step_types"] == ["load_project", "run_lua", "<redacted>"]

    serialized = json.dumps(payload, sort_keys=True)
    assert "client_alpha_secret" not in serialized
    assert "operator_Operator_Wang" not in serialized
    assert "Operator_Wang" not in serialized


def test_inspect_h300_static_project_summarizes_media_and_programs(tmp_path: Path):
    project = create_h300_static_project_fixture(tmp_path / "project")

    payload = inspect_h300_static_project(project).to_dict()

    assert payload["images"] == [
        {
            "path_pattern": "project_<redacted>_image/project_<redacted>_part_<timestamp>.jpg",
            "width": 17,
            "height": 11,
            "mode": "RGB",
        }
    ]
    assert payload["point_clouds"] == [
        {
            "path_pattern": "project_<redacted>_point_cloud/project_<redacted>_part_<timestamp>.pcd",
            "fields": ["x", "y", "z"],
            "width": 3,
            "height": 1,
            "points": 3,
            "data": "ascii",
        }
    ]
    assert payload["text_point_clouds"] == [
        {
            "path_pattern": "point_cloud/project_<redacted>.txt",
            "sampled_column_count": 4,
            "sampled_line_count": 2,
        }
    ]
    assert payload["lua_program"]["command_counts"]["MoveAbsJ"] == 1
    assert payload["lua_program"]["command_counts"]["MoveL"] == 1
    assert payload["lua_program"]["command_counts"]["ArcMPL"] == 1
    assert payload["lua_program"]["command_counts"]["Stop"] == 1
    assert payload["lua_program"]["definition_counts"]["ROBTARGET"] == 1
    assert payload["lua_program"]["definition_counts"]["JOINTTARGET"] == 1
    assert payload["lua_program"]["definition_counts"]["SEAMDATA"] == 1
    assert payload["lua_program"]["definition_counts"]["WELDDATA"] == 1
    assert payload["lua_program"]["definition_counts"]["WEAVEDATA"] == 1
    assert payload["lua_program"]["definition_counts"]["MULTIPASSDATA"] == 1
    assert payload["flow_config"]["step_count"] == 2
    assert payload["flow_config"]["step_types"] == ["load_project", "run_lua"]


def test_inspect_h300_static_project_summarizes_weld_seams_and_gaps(tmp_path: Path):
    project = create_h300_static_project_fixture(tmp_path / "project")

    payload = inspect_h300_static_project(project).to_dict()

    assert payload["weld_seams"]["seam_count"] == 2
    assert payload["weld_seams"]["type_distribution"] == {"butt": 1, "fillet": 1}
    assert payload["weld_seams"]["orientation_distribution"] == {"left": 1, "right": 1}
    assert payload["weld_seams"]["weld_type_distribution"] == {"arc": 2}
    assert payload["weld_seams"]["segment_count"] == 3
    assert payload["weld_seams"]["measured_width_count"] == 3

    gap_ids = {gap["gap_id"] for gap in payload["gap_mapping"]}
    assert gap_ids == {
        "G-001",
        "G-003",
        "G-004",
        "G-005",
        "G-006",
        "G-007",
        "G-008",
        "G-010",
        "G-012",
    }


def test_inspect_h300_static_project_rejects_missing_directory(tmp_path: Path):
    missing = tmp_path / "missing"

    with pytest.raises(FileNotFoundError) as exc_info:
        inspect_h300_static_project(missing)

    assert str(exc_info.value) == "H300 static project directory not found."
    assert str(missing) not in str(exc_info.value)
