from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
_SAFE_FILE_SUFFIXES = _IMAGE_SUFFIXES | {".json", ".pcd", ".txt", ".lua", ".md", ".csv"}
_COMMAND_NAMES = ("MoveAbsJ", "MoveL", "ArcMPL", "Stop")
_DEFINITION_NAMES = ("ROBTARGET", "JOINTTARGET", "SEAMDATA", "WELDDATA", "WEAVEDATA", "MULTIPASSDATA")
_GAP_IDS = ("G-001", "G-003", "G-004", "G-005", "G-006", "G-007", "G-008", "G-010", "G-012")
_PROJECT_TOP_LEVEL_KEY_ALLOWLIST = (
    "calibration",
    "camera",
    "extractPathPlan",
    "info",
    "pathPlan",
    "photoPoses",
    "processes",
    "robot",
    "runtime",
)
_SAFE_FIELD_LABELS = {
    "dataroot": "data_root",
    "device_id": "device_id",
    "deviceid": "device_id",
    "path": "path",
    "port": "port",
    "program": "program",
    "server": "server",
}
_SAFE_LABELS = {
    "arc": "arc",
    "ascii": "ascii",
    "binary": "binary",
    "binary_compressed": "binary_compressed",
    "butt": "butt",
    "fillet": "fillet",
    "horizontal": "horizontal",
    "left": "left",
    "line": "line",
    "load_project": "load_project",
    "plate": "plate",
    "right": "right",
    "run_lua": "run_lua",
    "vertical": "vertical",
}
_SAFE_PCD_FIELD_LABELS = {
    "b": "b",
    "curvature": "curvature",
    "g": "g",
    "intensity": "intensity",
    "label": "label",
    "normal_x": "normal_x",
    "normal_y": "normal_y",
    "normal_z": "normal_z",
    "r": "r",
    "rgb": "rgb",
    "rgba": "rgba",
    "ring": "ring",
    "timestamp": "timestamp",
    "x": "x",
    "y": "y",
    "z": "z",
}
_PERSON_FIELD_RE = re.compile(r"(operator|author|reviewer|person|user)", re.IGNORECASE)
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:[\\/]")


@dataclass(frozen=True)
class H300StaticFile:
    path_pattern: str
    extension: str
    size_bytes: int
    role: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_pattern": self.path_pattern,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "role": self.role,
        }


@dataclass(frozen=True)
class H300ImageSummary:
    path_pattern: str
    width: int
    height: int
    mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_pattern": self.path_pattern,
            "width": self.width,
            "height": self.height,
            "mode": self.mode,
        }


@dataclass(frozen=True)
class H300PointCloudSummary:
    path_pattern: str
    fields: list[str]
    width: int | None
    height: int | None
    points: int | None
    data: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_pattern": self.path_pattern,
            "fields": list(self.fields),
            "width": self.width,
            "height": self.height,
            "points": self.points,
            "data": self.data,
        }


@dataclass(frozen=True)
class H300TextPointCloudSummary:
    path_pattern: str
    sampled_column_count: int | None
    sampled_line_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_pattern": self.path_pattern,
            "sampled_column_count": self.sampled_column_count,
            "sampled_line_count": self.sampled_line_count,
        }


@dataclass(frozen=True)
class H300WeldSeamSummary:
    seam_count: int
    type_distribution: dict[str, int]
    orientation_distribution: dict[str, int]
    weld_type_distribution: dict[str, int]
    segment_count: int
    measured_width_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "seam_count": self.seam_count,
            "type_distribution": dict(self.type_distribution),
            "orientation_distribution": dict(self.orientation_distribution),
            "weld_type_distribution": dict(self.weld_type_distribution),
            "segment_count": self.segment_count,
            "measured_width_count": self.measured_width_count,
        }


@dataclass(frozen=True)
class H300PathPlanSummary:
    path_plan_count: int
    extract_path_plan_count: int
    photo_pose_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_plan_count": self.path_plan_count,
            "extract_path_plan_count": self.extract_path_plan_count,
            "photo_pose_count": self.photo_pose_count,
        }


@dataclass(frozen=True)
class H300LuaProgramSummary:
    path_pattern: str
    command_counts: dict[str, int]
    definition_counts: dict[str, int]
    welding_action_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_pattern": self.path_pattern,
            "command_counts": dict(self.command_counts),
            "definition_counts": dict(self.definition_counts),
            "welding_action_count": self.welding_action_count,
        }


@dataclass(frozen=True)
class H300FlowConfigSummary:
    path_pattern: str
    step_count: int
    step_types: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_pattern": self.path_pattern,
            "step_count": self.step_count,
            "step_types": list(self.step_types),
        }


@dataclass(frozen=True)
class H300SensitivityFinding:
    finding_type: str
    path_pattern: str
    field: str | None
    severity: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "finding_type": self.finding_type,
            "path_pattern": self.path_pattern,
            "severity": self.severity,
            "message": self.message,
        }
        if self.field is not None:
            payload["field"] = self.field
        return payload


@dataclass(frozen=True)
class H300GapMapping:
    gap_id: str
    status: str
    evidence: list[str]
    next_step: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "status": self.status,
            "evidence": list(self.evidence),
            "next_step": self.next_step,
        }


@dataclass(frozen=True)
class H300StaticProjectReport:
    project_root: Path
    root_label: str
    recognized: bool
    project_info: dict[str, Any]
    files: list[H300StaticFile]
    images: list[H300ImageSummary]
    point_clouds: list[H300PointCloudSummary]
    text_point_clouds: list[H300TextPointCloudSummary]
    weld_seams: H300WeldSeamSummary
    path_plans: H300PathPlanSummary
    lua_program: H300LuaProgramSummary | None
    flow_config: H300FlowConfigSummary | None
    sensitivity_findings: list[H300SensitivityFinding]
    gap_mapping: list[H300GapMapping]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_label": self.root_label,
            "recognized": self.recognized,
            "project_info": dict(self.project_info),
            "files": [file.to_dict() for file in self.files],
            "images": [image.to_dict() for image in self.images],
            "point_clouds": [cloud.to_dict() for cloud in self.point_clouds],
            "text_point_clouds": [cloud.to_dict() for cloud in self.text_point_clouds],
            "weld_seams": self.weld_seams.to_dict(),
            "path_plans": self.path_plans.to_dict(),
            "lua_program": self.lua_program.to_dict() if self.lua_program is not None else None,
            "flow_config": self.flow_config.to_dict() if self.flow_config is not None else None,
            "sensitivity_findings": [finding.to_dict() for finding in self.sensitivity_findings],
            "gap_mapping": [gap.to_dict() for gap in self.gap_mapping],
            "summary": dict(self.summary),
        }


def inspect_h300_static_project(project: str | Path) -> H300StaticProjectReport:
    project_root = Path(project)
    if not project_root.is_dir():
        raise FileNotFoundError(f"H300 static project directory not found: {project_root}")

    all_files = sorted(path for path in project_root.rglob("*") if path.is_file())
    json_payloads: list[tuple[Path, dict[str, Any]]] = []
    findings: list[H300SensitivityFinding] = []
    for path in all_files:
        path_pattern = _redact_path_pattern(path, project_root)
        if _contains_sensitive_value(path.name):
            findings.append(_finding("sensitive_basename", path_pattern, None, "review", "File name contains review-only identifiers."))
        if path.suffix.lower() == ".json":
            payload = _read_json(path)
            if payload is not None:
                json_payloads.append((path, payload))
                findings.extend(_scan_payload_for_sensitivity(payload, path_pattern))
        elif path.suffix.lower() == ".lua":
            findings.append(_finding("source_artifact", path_pattern, None, "review", "Lua program is source artifact content."))
            findings.extend(_scan_text_for_sensitivity(_read_text(path), path_pattern))
        elif path.suffix.lower() in _IMAGE_SUFFIXES or path.suffix.lower() in {".pcd", ".txt"}:
            findings.append(_finding("source_artifact", path_pattern, None, "review", "Media or point cloud source artifact requires local review."))

    project_json = _select_project_json(json_payloads)
    campcd_json = _select_campcd_json(json_payloads)
    recipe_json = _select_recipe_json(json_payloads)
    flow_json = _select_flow_json(json_payloads)

    project_info = _summarize_project(project_json[1] if project_json else {})
    path_plans = H300PathPlanSummary(
        path_plan_count=int(project_info["path_plan_count"]),
        extract_path_plan_count=int(project_info["extract_path_plan_count"]),
        photo_pose_count=int(project_info["photo_pose_count"]),
    )
    if campcd_json is not None:
        project_info.update(_summarize_campcd(campcd_json[1]))

    files = [_summarize_file(path, project_root) for path in all_files]
    images: list[H300ImageSummary] = []
    for path in all_files:
        if path.suffix.lower() not in _IMAGE_SUFFIXES:
            continue
        image_summary = _summarize_image(path, project_root)
        if image_summary is None:
            findings.append(
                _finding(
                    "parse_error",
                    _redact_path_pattern(path, project_root),
                    None,
                    "review",
                    "Image file could not be parsed; summary skipped.",
                )
            )
        else:
            images.append(image_summary)
    point_clouds = [_summarize_pcd(path, project_root) for path in all_files if path.suffix.lower() == ".pcd"]
    text_point_clouds = [
        _summarize_text_point_cloud(path, project_root)
        for path in all_files
        if path.suffix.lower() == ".txt" and "point_cloud" in path.parts
    ]
    weld_seams = _summarize_weld_seams(recipe_json[1] if recipe_json else {})
    lua_program = _summarize_lua(_select_lua_file(all_files), project_root)
    flow_config = _summarize_flow(flow_json, project_root)

    summary = {
        "file_count": len(files),
        "image_count": len(images),
        "point_cloud_count": len(point_clouds),
        "text_point_cloud_count": len(text_point_clouds),
        "weld_seam_count": weld_seams.seam_count,
        "path_plan_count": path_plans.path_plan_count,
        "extract_path_plan_count": path_plans.extract_path_plan_count,
        "photo_pose_count": path_plans.photo_pose_count,
        "lua_arc_mpl_count": lua_program.command_counts.get("ArcMPL", 0) if lua_program is not None else 0,
        "flow_step_count": flow_config.step_count if flow_config is not None else 0,
        "sensitivity_finding_count": len(findings),
    }
    recognized = bool(project_json or campcd_json or recipe_json or images or point_clouds or lua_program)

    return H300StaticProjectReport(
        project_root=project_root,
        root_label="<local-project>",
        recognized=recognized,
        project_info=project_info,
        files=files,
        images=images,
        point_clouds=point_clouds,
        text_point_clouds=text_point_clouds,
        weld_seams=weld_seams,
        path_plans=path_plans,
        lua_program=lua_program,
        flow_config=flow_config,
        sensitivity_findings=findings,
        gap_mapping=_build_gap_mapping(),
        summary=summary,
    )


def _summarize_file(path: Path, project_root: Path) -> H300StaticFile:
    return H300StaticFile(
        path_pattern=_redact_path_pattern(path, project_root),
        extension=_safe_file_suffix(path.suffix),
        size_bytes=path.stat().st_size,
        role=_guess_role(path),
    )


def _summarize_project(payload: dict[str, Any]) -> dict[str, Any]:
    info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
    return {
        "has_project_name": bool(info.get("projectName")),
        "is_template": info.get("isTemplate") if isinstance(info.get("isTemplate"), bool) else None,
        "workpiece_seam_type": _safe_label(info.get("workpieceSeamType")),
        "known_top_level_keys": [key for key in _PROJECT_TOP_LEVEL_KEY_ALLOWLIST if key in payload],
        "top_level_key_count": len(payload),
        "photo_pose_count": _count_list(payload.get("photoPoses")),
        "path_plan_count": _count_list(payload.get("pathPlan")),
        "extract_path_plan_count": _count_list(payload.get("extractPathPlan")),
    }


def _summarize_campcd(payload: dict[str, Any]) -> dict[str, Any]:
    pcd_with_cam = payload.get("pcdWithCam")
    entries = pcd_with_cam if isinstance(pcd_with_cam, list) else []
    return {
        "campcd_pcd_with_cam_count": len(entries),
        "campcd_roi_enabled": any(_roi_enabled(entry) for entry in entries if isinstance(entry, dict)),
    }


def _summarize_image(path: Path, project_root: Path) -> H300ImageSummary | None:
    try:
        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
    except (OSError, ValueError):
        return None
    return H300ImageSummary(_redact_path_pattern(path, project_root), width, height, mode)


def _summarize_pcd(path: Path, project_root: Path) -> H300PointCloudSummary:
    header: dict[str, str] = {}
    with path.open("rb") as handle:
        for raw_line in handle:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition(" ")
            header[key.upper()] = value.strip()
            if key.upper() == "DATA":
                break
    return H300PointCloudSummary(
        path_pattern=_redact_path_pattern(path, project_root),
        fields=[_safe_pcd_field(field) for field in header.get("FIELDS", "").split()],
        width=_int_or_none(header.get("WIDTH")),
        height=_int_or_none(header.get("HEIGHT")),
        points=_int_or_none(header.get("POINTS")),
        data=_safe_label(header.get("DATA")),
    )


def _summarize_text_point_cloud(path: Path, project_root: Path) -> H300TextPointCloudSummary:
    sampled_lines: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                sampled_lines.append(stripped)
            if len(sampled_lines) >= 32:
                break
    column_count = len(sampled_lines[0].split()) if sampled_lines else None
    return H300TextPointCloudSummary(_redact_path_pattern(path, project_root), column_count, len(sampled_lines))


def _summarize_weld_seams(payload: dict[str, Any]) -> H300WeldSeamSummary:
    seams = payload.get("weld_seams")
    seam_rows = [seam for seam in seams if isinstance(seam, dict)] if isinstance(seams, list) else []
    type_counts: Counter[str] = Counter()
    orientation_counts: Counter[str] = Counter()
    weld_type_counts: Counter[str] = Counter()
    segment_count = 0
    measured_width_count = 0
    for seam in seam_rows:
        _count_safe_value(type_counts, seam.get("type"))
        _count_safe_value(orientation_counts, seam.get("orientation"))
        _count_safe_value(weld_type_counts, seam.get("weld_type"))
        segment_count += _count_list(seam.get("segments"))
        measured_width_count += _count_list(seam.get("measured_widths"))
    return H300WeldSeamSummary(
        seam_count=len(seam_rows),
        type_distribution=dict(sorted(type_counts.items())),
        orientation_distribution=dict(sorted(orientation_counts.items())),
        weld_type_distribution=dict(sorted(weld_type_counts.items())),
        segment_count=segment_count,
        measured_width_count=measured_width_count,
    )


def _summarize_lua(path: Path | None, project_root: Path) -> H300LuaProgramSummary | None:
    if path is None:
        return None
    text = _read_text(path)
    command_counts = {
        command: len(re.findall(rf"\b{re.escape(command)}\b", text, flags=re.IGNORECASE))
        for command in _COMMAND_NAMES
    }
    definition_counts = {
        definition: len(re.findall(rf"\b{re.escape(definition)}\b", text, flags=re.IGNORECASE))
        for definition in _DEFINITION_NAMES
    }
    return H300LuaProgramSummary(
        path_pattern=_redact_path_pattern(path, project_root),
        command_counts=command_counts,
        definition_counts=definition_counts,
        welding_action_count=command_counts["ArcMPL"],
    )


def _summarize_flow(flow_json: tuple[Path, dict[str, Any]] | None, project_root: Path) -> H300FlowConfigSummary | None:
    if flow_json is None:
        return None
    path, payload = flow_json
    flow = payload.get("flow")
    steps = flow if isinstance(flow, list) else []
    step_types = []
    for step in steps:
        if isinstance(step, dict):
            step_type = _safe_label(step.get("type"))
            if step_type is not None:
                step_types.append(step_type)
    return H300FlowConfigSummary(_redact_path_pattern(path, project_root), len(steps), step_types)


def _build_gap_mapping() -> list[H300GapMapping]:
    next_steps = {
        "G-001": "Review project identifiers as trace clues only.",
        "G-003": "Review point cloud coordinate frames and source artifact handling.",
        "G-004": "Review image, camera, and calibration redaction boundaries.",
        "G-005": "Keep model or algorithm outputs as source artifacts until mapped.",
        "G-006": "Review manual teaching or operator fields before label mapping.",
        "G-007": "Treat weld process templates as static configuration, not runtime samples.",
        "G-008": "Treat Lua and flow order as execution plan clues, not event logs.",
        "G-010": "Review local storage and offline download retention policy.",
        "G-012": "Review coordinate system, TCP, camera pose, frame, and unit conventions.",
    }
    return [
        H300GapMapping(gap_id=gap_id, status="needs_review", evidence=["static_project_summary"], next_step=next_steps[gap_id])
        for gap_id in _GAP_IDS
    ]


def _select_project_json(json_payloads: list[tuple[Path, dict[str, Any]]]) -> tuple[Path, dict[str, Any]] | None:
    for path, payload in json_payloads:
        if path.parent.name == "campcd_json" and path.name.endswith("_campcd.json"):
            continue
        if {"info", "pathPlan", "extractPathPlan"} & set(payload):
            return path, payload
    return None


def _select_campcd_json(json_payloads: list[tuple[Path, dict[str, Any]]]) -> tuple[Path, dict[str, Any]] | None:
    for path, payload in json_payloads:
        if path.name.endswith("_campcd.json") or "pcdWithCam" in payload:
            return path, payload
    return None


def _select_recipe_json(json_payloads: list[tuple[Path, dict[str, Any]]]) -> tuple[Path, dict[str, Any]] | None:
    for path, payload in json_payloads:
        if path.parent.name == "weld_seam" or "weld_seams" in payload:
            return path, payload
    return None


def _select_flow_json(json_payloads: list[tuple[Path, dict[str, Any]]]) -> tuple[Path, dict[str, Any]] | None:
    for path, payload in json_payloads:
        if "flow" in payload or "weld_config" in path.parent.name:
            return path, payload
    return None


def _select_lua_file(all_files: list[Path]) -> Path | None:
    return next((path for path in all_files if path.suffix.lower() == ".lua"), None)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _scan_payload_for_sensitivity(payload: dict[str, Any], path_pattern: str) -> list[H300SensitivityFinding]:
    findings: list[H300SensitivityFinding] = []

    def visit(value: Any, field: str | None = None) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                if _PERSON_FIELD_RE.search(key_text):
                    findings.append(_finding("person_field", path_pattern, key_text, "review", "Person-like field requires redaction review."))
                if key_text.lower() in {"port", "server", "device_id", "deviceid"}:
                    findings.append(_finding("network_or_device_field", path_pattern, key_text, "review", "Network or device field requires redaction review."))
                visit(child, key_text)
        elif isinstance(value, list):
            for child in value:
                visit(child, field)
        elif isinstance(value, str):
            findings.extend(_scan_text_for_sensitivity(value, path_pattern, field))
    visit(payload)
    return findings


def _scan_text_for_sensitivity(text: str, path_pattern: str, field: str | None = None) -> list[H300SensitivityFinding]:
    findings: list[H300SensitivityFinding] = []
    if _WINDOWS_PATH_RE.search(text):
        findings.append(_finding("windows_path", path_pattern, field, "review", "Windows absolute path requires redaction review."))
    if _IP_RE.search(text):
        findings.append(_finding("ip_address", path_pattern, field, "review", "IP address requires redaction review."))
    if re.search(r"\b\d{6,}\b", text):
        findings.append(_finding("timestamp_or_identifier", path_pattern, field, "review", "Timestamp or business identifier requires redaction review."))
    return findings


def _contains_sensitive_value(text: str) -> bool:
    return bool(_WINDOWS_PATH_RE.search(text) or _IP_RE.search(text) or re.search(r"\b(?:\d{6,}|22222)\b", text))


def _redact_path_pattern(path: Path, project_root: Path) -> str:
    try:
        relative = path.relative_to(project_root)
    except ValueError:
        relative = Path(path.name)
    return "/".join(
        _redact_path_part(part, is_file=index == len(relative.parts) - 1)
        for index, part in enumerate(relative.parts)
    )


def _redact_path_part(name: str, *, is_file: bool) -> str:
    if is_file:
        return _redact_file_basename(name)
    return _redact_directory_basename(name)


def _redact_directory_basename(name: str) -> str:
    path = Path(name)
    lowered = path.stem.lower()
    if lowered in {"campcd_json", "point_cloud", "weld_seam"}:
        return lowered
    if lowered.startswith("project_"):
        if lowered.endswith("_image"):
            return "project_<redacted>_image"
        if lowered.endswith("_point_cloud"):
            return "project_<redacted>_point_cloud"
    if lowered.endswith("_weld_config"):
        return "weld_config"
    if lowered.endswith("_lua_script"):
        return "lua_script"
    return "<redacted>"


def _redact_file_basename(name: str) -> str:
    path = Path(name)
    stem = path.stem
    suffix = _safe_file_suffix(path.suffix)
    lowered = stem.lower()
    if lowered.startswith("project_"):
        if "_part_" in lowered:
            return f"project_<redacted>_part_<timestamp>{suffix}"
        if lowered.endswith("_image"):
            return "project_<redacted>_image"
        if lowered.endswith("_point_cloud"):
            return "project_<redacted>_point_cloud"
        if lowered.endswith("_campcd"):
            return f"project_<redacted>_campcd{suffix}"
        return f"project_<redacted>{suffix}"
    if lowered.startswith("recipe2_project_") or lowered.startswith("recipe_project_"):
        return re.sub(r"project_.+", "project_<redacted>", stem) + suffix
    return f"<redacted>{suffix}"


def _safe_file_suffix(suffix: str) -> str:
    if not suffix:
        return ""
    lowered = suffix.lower()
    if lowered in _SAFE_FILE_SUFFIXES:
        return lowered
    return "<redacted_extension>"


def _safe_label(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if _contains_sensitive_value(value):
        return "<redacted>"
    return _SAFE_LABELS.get(value.strip().lower(), "<redacted>")


def _safe_pcd_field(value: str) -> str:
    if _contains_sensitive_value(value):
        return "<redacted>"
    return _SAFE_PCD_FIELD_LABELS.get(value.strip().lower(), "<redacted>")


def _count_safe_value(counter: Counter[str], value: Any) -> None:
    label = _safe_label(value)
    if label is not None:
        counter[label] += 1


def _guess_role(path: Path) -> str:
    suffix = path.suffix.lower()
    parent = path.parent.name
    if suffix in _IMAGE_SUFFIXES:
        return "image"
    if suffix == ".pcd":
        return "point_cloud_pcd"
    if suffix == ".txt" and "point_cloud" in path.parts:
        return "point_cloud_text"
    if suffix == ".lua":
        return "lua_program"
    if parent == "weld_seam":
        return "weld_seam_recipe"
    if parent == "campcd_json" and path.name.endswith("_campcd.json"):
        return "campcd_index"
    if parent == "campcd_json" and suffix == ".json":
        return "project_json"
    if "weld_config" in parent:
        return "flow_config"
    return "source_artifact"


def _roi_enabled(entry: dict[str, Any]) -> bool:
    roi = entry.get("roi")
    return bool(isinstance(roi, dict) and roi.get("enabled"))


def _count_list(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _finding(
    finding_type: str,
    path_pattern: str,
    field: str | None,
    severity: str,
    message: str,
) -> H300SensitivityFinding:
    return H300SensitivityFinding(finding_type, path_pattern, _normalize_finding_field(field), severity, message)


def _normalize_finding_field(field: str | None) -> str | None:
    if field is None:
        return None
    if _PERSON_FIELD_RE.search(field):
        return "person_field"
    return _SAFE_FIELD_LABELS.get(field.lower(), "<redacted_field>")
