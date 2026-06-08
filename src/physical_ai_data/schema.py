from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = "physical-ai-package/v0.1"

SUPPORTED_SCENARIOS = {"robot_welding_station", "arm_pick_sort"}

REQUIRED_MANIFEST_FIELDS = [
    "schema_version",
    "package_id",
    "scenario_type",
    "created_at",
    "task",
    "devices",
    "objects",
    "coordinate_frames",
    "timelines",
    "tables",
    "artifacts",
]

REQUIRED_TABLE_COLUMNS = {
    "frames": [
        "frame_id",
        "timestamp_s",
        "timeline",
        "phase",
        "coordinate_frame_id",
        "robot_state_ref",
        "tcp_pose_ref",
        "image_ref",
        "point_cloud_ref",
        "trajectory_ref",
    ],
    "events": [
        "event_id",
        "timestamp_s",
        "event_type",
        "severity",
        "message",
        "related_frame_id",
        "related_object_id",
    ],
    "labels": [
        "label_id",
        "label_type",
        "target_ref",
        "value",
        "confidence",
        "source",
    ],
    "metrics": [
        "metric_id",
        "timestamp_s",
        "metric_name",
        "value",
        "unit",
        "source",
    ],
}

CANDIDATE_COLUMNS = [
    "candidate_id",
    "source_type",
    "source_id",
    "frame_id",
    "object_id",
    "timestamp_s",
    "reasons",
    "score",
]


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    message: str
    path: str = ""


@dataclass
class ValidationResult:
    errors: list[ValidationMessage] = field(default_factory=list)
    warnings: list[ValidationMessage] = field(default_factory=list)
    summary: dict[str, object] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors
