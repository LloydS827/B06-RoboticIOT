from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeRobotProfile:
    name: str
    phase: str = "episode"

    def object_ids(self) -> list[dict[str, str]]:
        return [{"object_id": "task_object", "type": "object"}]


class PushTProfile(LeRobotProfile):
    def __init__(self) -> None:
        super().__init__(name="pusht", phase="pushing")

    def object_ids(self) -> list[dict[str, str]]:
        return [
            {"object_id": "block", "type": "object"},
            {"object_id": "target", "type": "target"},
        ]


class AlohaProfile(LeRobotProfile):
    def __init__(self) -> None:
        super().__init__(name="aloha", phase="manipulation")


class FallbackProfile(LeRobotProfile):
    def __init__(self) -> None:
        super().__init__(name="fallback", phase="episode")


def select_lerobot_profile(repo_id: str, requested: str = "auto") -> LeRobotProfile:
    normalized = requested.lower()
    if normalized == "auto":
        repo_id_lower = repo_id.lower()
        if "pusht" in repo_id_lower:
            return PushTProfile()
        if "aloha" in repo_id_lower:
            return AlohaProfile()
        return FallbackProfile()
    if normalized == "pusht":
        return PushTProfile()
    if normalized == "aloha":
        return AlohaProfile()
    if normalized == "fallback":
        return FallbackProfile()
    raise ValueError(f"Unsupported LeRobot profile: {requested}")
