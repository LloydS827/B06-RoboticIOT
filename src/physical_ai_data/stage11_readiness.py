from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CHECK_PASS = "pass"
CHECK_REVIEW = "review"
CHECK_BLOCK = "block"

OVERALL_READY = "ready_for_pipeline_smoke"
OVERALL_REVIEW = "review_required"
OVERALL_BLOCKED = "blocked"

GAP_READY = "ready_to_review"
GAP_RAW_REVIEW = "needs_raw_review"
GAP_BLOCKED = "blocked"
GAP_NOT_APPLICABLE = "not_applicable"

REQUIRED_CLEAN_FILES = ("job.json", "frames.csv", "process.csv", "events.csv")
TCP_POSE_COLUMNS = ("tcp_x", "tcp_y", "tcp_z")
JOB_ID_KEYS = ("job_window_id", "task_id", "work_order_id", "job_id")

_RAW_EVIDENCE_PATHS = {
    "G-003": ("files/point_clouds/window_0000.pcd", "files/pcl_seam_candidates.json"),
    "G-004": ("files/images/front_0000.png",),
    "G-005": ("files/model_outputs.json",),
    "G-009": ("files/quality_result.json",),
    "G-011": ("tcp_json/hmi_task_messages.ndjson",),
    "G-012": ("files/seam_trajectory.json", "files/pcl_seam_candidates.json"),
}


@dataclass(frozen=True)
class ReadinessCheck:
    check_id: str
    status: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "check_id": self.check_id,
            "status": self.status,
            "message": self.message,
        }
        if self.path is not None:
            payload["path"] = self.path
        return payload


@dataclass(frozen=True)
class GapStatus:
    gap_id: str
    status: str
    evidence: list[str]
    next_step: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "status": self.status,
            "evidence": self.evidence,
            "next_step": self.next_step,
        }


@dataclass(frozen=True)
class H300ReadinessReport:
    clean_root: Path
    raw_root: Path | None
    overall_status: str
    checks: list[ReadinessCheck]
    gap_statuses: list[GapStatus]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean_root": str(self.clean_root),
            "raw_root": str(self.raw_root) if self.raw_root is not None else None,
            "overall_status": self.overall_status,
            "checks": [check.to_dict() for check in self.checks],
            "gap_statuses": [gap.to_dict() for gap in self.gap_statuses],
            "summary": dict(self.summary),
        }


def assess_h300_sample_readiness(
    clean_root: str | Path,
    raw_root: str | Path | None = None,
) -> H300ReadinessReport:
    clean_path = Path(clean_root)
    raw_path = Path(raw_root) if raw_root is not None else None
    checks: list[ReadinessCheck] = []

    required_present = _check_required_clean_files(clean_path, checks)
    job_payload = _load_job(clean_path / "job.json")
    job_id_clue_present = _has_job_id_clue(job_payload)
    checks.append(
        ReadinessCheck(
            "job:id_fields",
            CHECK_PASS if job_id_clue_present else CHECK_BLOCK,
            "job.json contains a job/task/window identifier"
            if job_id_clue_present
            else "job.json must contain at least one job identifier clue",
            str(clean_path / "job.json"),
        )
    )

    frames_rows, frames_headers, frames_error = _read_csv_rows(clean_path / "frames.csv")
    frame_count = len(frames_rows)
    frames_readable = frames_headers is not None and frames_error is None
    if not frames_readable:
        checks.append(
            ReadinessCheck("frames:readable", CHECK_BLOCK, "frames.csv must be readable with headers", str(clean_path / "frames.csv"))
        )
    else:
        checks.append(ReadinessCheck("frames:readable", CHECK_PASS, "frames.csv is readable", str(clean_path / "frames.csv")))

    frames_has_rows = bool(frames_rows)
    checks.append(
        ReadinessCheck(
            "frames:rows",
            CHECK_PASS if frames_has_rows else CHECK_BLOCK,
            "frames.csv contains frame rows" if frames_has_rows else "frames.csv must contain at least one frame row",
            str(clean_path / "frames.csv"),
        )
    )

    frames_has_timestamp = bool(frames_headers and "timestamp_s" in frames_headers)
    checks.append(
        ReadinessCheck(
            "frames:timestamp_s",
            CHECK_PASS if frames_has_timestamp else CHECK_BLOCK,
            "frames.csv includes timestamp_s" if frames_has_timestamp else "frames.csv must include timestamp_s",
            str(clean_path / "frames.csv"),
        )
    )

    frames_has_tcp_pose = bool(frames_headers and all(column in frames_headers for column in TCP_POSE_COLUMNS))
    checks.append(
        ReadinessCheck(
            "frames:tcp_pose",
            CHECK_PASS if frames_has_tcp_pose else CHECK_BLOCK,
            "frames.csv includes TCP pose columns" if frames_has_tcp_pose else "frames.csv must include tcp_x, tcp_y, and tcp_z",
            str(clean_path / "frames.csv"),
        )
    )

    _check_frame_image_paths(clean_path, frames_rows, frames_headers, checks)
    process_header_ok = _check_csv_header(clean_path / "process.csv", "process.csv", checks)
    events_header_ok = _check_csv_header(clean_path / "events.csv", "events.csv", checks)
    review_labels_exists = _check_review_labels(clean_path, checks)
    raw_evidence = _check_raw_evidence(raw_path, checks)

    gap_statuses = _build_gap_statuses(
        job_id_clue_present=job_id_clue_present,
        frames_timeline_ok=frames_has_timestamp and frames_has_tcp_pose,
        process_header_ok=process_header_ok,
        events_header_ok=events_header_ok,
        review_labels_exists=review_labels_exists,
        raw_evidence=raw_evidence,
    )
    overall_status = _overall_status(checks)
    summary = {
        "clean_required_files_present": required_present,
        "frame_count": frame_count,
        "job_id_clue_present": job_id_clue_present,
        "review_labels_present": review_labels_exists,
        "raw_root_provided": raw_path is not None,
    }

    return H300ReadinessReport(
        clean_root=clean_path,
        raw_root=raw_path,
        overall_status=overall_status,
        checks=checks,
        gap_statuses=gap_statuses,
        summary=summary,
    )


def _check_required_clean_files(clean_root: Path, checks: list[ReadinessCheck]) -> bool:
    all_present = True
    for name in REQUIRED_CLEAN_FILES:
        path = clean_root / name
        present = path.is_file()
        all_present = all_present and present
        checks.append(
            ReadinessCheck(
                f"clean_required:{name}",
                CHECK_PASS if present else CHECK_BLOCK,
                f"{name} is present" if present else f"{name} is required in the clean root",
                str(path),
            )
        )
    return all_present


def _read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str] | None, str | None]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return [], None, "missing header"
            return list(reader), list(reader.fieldnames), None
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        return [], None, str(exc)


def _load_job(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _has_job_id_clue(payload: dict[str, Any]) -> bool:
    if any(key in payload and payload[key] for key in JOB_ID_KEYS):
        return True
    for container_key in ("job", "window"):
        nested = payload.get(container_key)
        if isinstance(nested, dict) and any(key in nested and nested[key] for key in JOB_ID_KEYS):
            return True
    return False


def _check_frame_image_paths(
    clean_root: Path,
    rows: list[dict[str, str]],
    headers: list[str] | None,
    checks: list[ReadinessCheck],
) -> None:
    if not headers or "image_path" not in headers:
        return

    for row in rows:
        image_value = (row.get("image_path") or "").strip()
        if not image_value:
            continue
        if not _path_exists_within_root(clean_root, image_value):
            checks.append(
                ReadinessCheck(
                    "frames:image_path",
                    CHECK_BLOCK,
                    f"frames.csv image_path must stay within clean root and exist: {image_value}",
                    str(clean_root / image_value),
                )
            )
            return
    checks.append(ReadinessCheck("frames:image_path", CHECK_PASS, "frames.csv image references are local and present", str(clean_root)))


def _path_exists_within_root(root: Path, relative_path: str) -> bool:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        return False
    candidate = root / path
    if not candidate.is_file():
        return False
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        return False
    return True


def _check_csv_header(path: Path, label: str, checks: list[ReadinessCheck]) -> bool:
    _rows, headers, error = _read_csv_rows(path)
    header_ok = headers is not None and error is None
    checks.append(
        ReadinessCheck(
            f"{label}:header",
            CHECK_PASS if header_ok else CHECK_BLOCK,
            f"{label} includes a CSV header" if header_ok else f"{label} must be readable with a CSV header",
            str(path),
        )
    )
    return header_ok


def _check_review_labels(clean_root: Path, checks: list[ReadinessCheck]) -> bool:
    path = clean_root / "review_labels.csv"
    exists = path.is_file()
    checks.append(
        ReadinessCheck(
            "review_labels.csv",
            CHECK_REVIEW,
            "review_labels.csv is present and should be reviewed"
            if exists
            else "review_labels.csv is absent; human review labels are still needed",
            str(path),
        )
    )
    return exists


def _check_raw_evidence(raw_root: Path | None, checks: list[ReadinessCheck]) -> dict[str, bool]:
    evidence = {gap_id: False for gap_id in _RAW_EVIDENCE_PATHS}
    if raw_root is None:
        return evidence

    manifest = raw_root / "manifest.raw.json"
    manifest_ok = _raw_manifest_readable(raw_root / "manifest.raw.json")
    checks.append(
        ReadinessCheck(
            "raw:manifest.raw.json",
            CHECK_REVIEW,
            "raw manifest is present for source review" if manifest_ok else "raw manifest is missing or unreadable; source review required",
            str(manifest),
        )
    )

    for gap_id, paths in _RAW_EVIDENCE_PATHS.items():
        exists = _raw_evidence(raw_root, paths)
        evidence[gap_id] = exists
        checks.append(
            ReadinessCheck(
                f"raw:{gap_id}",
                CHECK_REVIEW,
                f"{gap_id} raw/source evidence is present for review"
                if exists
                else f"{gap_id} raw/source evidence is missing and must be reviewed",
                str(raw_root),
            )
        )
    return evidence


def _raw_evidence(raw_root: Path, relative_paths: tuple[str, ...]) -> bool:
    return all((raw_root / relative_path).is_file() for relative_path in relative_paths)


def _raw_manifest_readable(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False
    return isinstance(payload, dict)


def _build_gap_statuses(
    *,
    job_id_clue_present: bool,
    frames_timeline_ok: bool,
    process_header_ok: bool,
    events_header_ok: bool,
    review_labels_exists: bool,
    raw_evidence: dict[str, bool],
) -> list[GapStatus]:
    return [
        _gap("G-001", GAP_READY if job_id_clue_present else GAP_BLOCKED, ["job.json"], "Confirm job/window identifiers."),
        _gap("G-002", GAP_READY if frames_timeline_ok else GAP_BLOCKED, ["frames.csv"], "Confirm timestamp and TCP pose coverage."),
        _raw_gap("G-003", raw_evidence),
        _raw_gap("G-004", raw_evidence),
        _raw_gap("G-005", raw_evidence),
        _gap(
            "G-006",
            GAP_READY if review_labels_exists else GAP_RAW_REVIEW,
            ["review_labels.csv"] if review_labels_exists else [],
            "Review human labels and correction provenance.",
        ),
        _gap("G-007", GAP_READY if process_header_ok else GAP_BLOCKED, ["process.csv"], "Review process telemetry columns."),
        _gap("G-008", GAP_READY if events_header_ok else GAP_BLOCKED, ["events.csv"], "Review event log coverage."),
        _gap(
            "G-009",
            GAP_RAW_REVIEW if review_labels_exists or raw_evidence["G-009"] else GAP_BLOCKED,
            ["review_labels.csv"] if review_labels_exists else _evidence_paths("G-009", raw_evidence),
            "Review quality labels or raw quality inspection evidence.",
        ),
        _gap("G-010", GAP_RAW_REVIEW, [], "Review source capture and replacement protocol."),
        _raw_gap("G-011", raw_evidence),
        _raw_gap("G-012", raw_evidence),
    ]


def _raw_gap(gap_id: str, raw_evidence: dict[str, bool]) -> GapStatus:
    return _gap(
        gap_id,
        GAP_RAW_REVIEW if raw_evidence[gap_id] else GAP_BLOCKED,
        _evidence_paths(gap_id, raw_evidence),
        "Review corresponding raw/source evidence.",
    )


def _evidence_paths(gap_id: str, raw_evidence: dict[str, bool]) -> list[str]:
    if not raw_evidence[gap_id]:
        return []
    return list(_RAW_EVIDENCE_PATHS[gap_id])


def _gap(gap_id: str, status: str, evidence: list[str], next_step: str) -> GapStatus:
    return GapStatus(gap_id=gap_id, status=status, evidence=evidence, next_step=next_step)


def _overall_status(checks: list[ReadinessCheck]) -> str:
    if any(check.status == CHECK_BLOCK for check in checks):
        return OVERALL_BLOCKED
    if any(check.status == CHECK_REVIEW for check in checks):
        return OVERALL_REVIEW
    return OVERALL_READY
