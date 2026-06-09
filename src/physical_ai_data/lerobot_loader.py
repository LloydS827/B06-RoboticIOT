from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
import tempfile
from typing import Any

import numpy as np
from PIL import Image

from physical_ai_data.lerobot_adapter import LeRobotEpisode, LeRobotFrame
from physical_ai_data.lerobot_profiles import select_lerobot_profile


def load_lerobot_episode(
    repo_id: str,
    episode_index: int,
    root: str | Path | None = None,
    profile: str = "auto",
    max_frames: int | None = None,
    camera: str | None = None,
) -> LeRobotEpisode:
    if max_frames is not None and max_frames <= 0:
        raise ValueError("max_frames must be positive")

    LeRobotDataset = _lerobot_dataset_class()

    root_path = Path(root) if root is not None else None
    dataset = _open_dataset(LeRobotDataset, repo_id, root_path, episode_index)
    selected_profile = select_lerobot_profile(repo_id, profile)

    frames: list[LeRobotFrame] = []
    first_row: Mapping[str, Any] | None = None
    for row in _dataset_rows(dataset):
        if not isinstance(row, Mapping):
            continue
        if not _matches_episode(row, episode_index):
            continue
        if first_row is None:
            first_row = row
        frames.append(_frame_from_row(row, len(frames), camera))
        if max_frames is not None and len(frames) >= max_frames:
            break

    return LeRobotEpisode(
        repo_id=repo_id,
        episode_index=episode_index,
        fps=_fps(dataset),
        task_name=_task_name(first_row),
        profile=selected_profile.name,
        root=root_path,
        features=_features(dataset),
        stats=_stats(dataset),
        episode_metadata=_episode_metadata(dataset, first_row, episode_index),
        task_metadata=_task_metadata(dataset, first_row),
        frames=frames,
    )


def _lerobot_dataset_class() -> Any:
    try:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset

        return LeRobotDataset
    except (ImportError, AttributeError) as current_exc:
        try:
            from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

            return LeRobotDataset
        except (ImportError, AttributeError) as legacy_exc:
            raise RuntimeError(
                "Install the lerobot optional dependency with `pip install '.[lerobot]'` "
                "to load real LeRobot datasets."
            ) from legacy_exc or current_exc


def _open_dataset(dataset_class: Any, repo_id: str, root: Path | None, episode_index: int) -> Any:
    try:
        return dataset_class(repo_id, root=root, episodes=[episode_index])
    except TypeError:
        try:
            return dataset_class(repo_id, root=root)
        except TypeError:
            return dataset_class(repo_id)


def _dataset_rows(dataset: Any) -> Iterable[Any]:
    hf_dataset = getattr(dataset, "hf_dataset", None)
    if hf_dataset is not None:
        return hf_dataset
    return dataset


def _matches_episode(row: Mapping[str, Any], episode_index: int) -> bool:
    row_episode = _first_value(row, ("episode_index", "episode.index", "episode"))
    if row_episode is None:
        return True
    try:
        return int(_scalar(row_episode)) == episode_index
    except (TypeError, ValueError):
        return False


def _frame_from_row(row: Mapping[str, Any], output_index: int, camera: str | None) -> LeRobotFrame:
    return LeRobotFrame(
        frame_index=_int_value(_first_value(row, ("frame_index", "frame.idx", "index")), output_index),
        timestamp_s=_optional_float(_first_value(row, ("timestamp", "timestamp_s"))),
        images=_image_refs(row, camera),
        state=_float_list(_first_value(row, ("observation.state", "state"))),
        action=_float_list(_first_value(row, ("action",))),
    )


def _image_refs(row: Mapping[str, Any], selected_camera: str | None) -> dict[str, Path]:
    images: dict[str, Path] = {}
    for key, value in row.items():
        is_image_key = "image" in key.lower()
        path = _path_like(value)
        if path is not None and not is_image_key and not _looks_like_image_path(path):
            continue
        camera = _camera_name(key, selected_camera)
        if selected_camera is not None and camera != selected_camera:
            continue
        if path is None and is_image_key:
            path = _temporary_image_path(value, camera)
        if path is None:
            continue
        images[camera] = path
    return images


def _camera_name(key: str, selected_camera: str | None) -> str:
    parts = [
        part
        for part in key.replace("/", ".").split(".")
        if part and part.lower() not in {"observation", "observations", "images", "image", "rgb"}
    ]
    if parts:
        return parts[-1]
    return selected_camera or "image"


def _path_like(value: Any) -> Path | None:
    normalized = _normalize(value)
    if isinstance(normalized, Path):
        return normalized
    if isinstance(normalized, str):
        return Path(normalized)
    return None


def _looks_like_image_path(path: Path) -> bool:
    return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def _temporary_image_path(value: Any, camera: str) -> Path | None:
    image = _pil_image(value)
    if image is None:
        return None
    output_dir = Path(tempfile.mkdtemp(prefix="physical_ai_lerobot_images_"))
    output_path = output_dir / f"{_safe_filename(camera)}.png"
    image.save(output_path)
    return output_path


def _pil_image(value: Any) -> Image.Image | None:
    if isinstance(value, Image.Image):
        return value
    array = _image_array(value)
    if array is None:
        return None
    return Image.fromarray(array)


def _image_array(value: Any) -> np.ndarray | None:
    normalized = _normalize(value)
    try:
        array = np.asarray(normalized)
    except (TypeError, ValueError):
        return None
    if array.ndim == 0:
        return None
    if array.dtype == object:
        try:
            array = array.astype(float)
        except (TypeError, ValueError):
            return None
    if array.ndim == 3:
        if array.shape[-1] in {1, 3}:
            pass
        elif array.shape[0] in {1, 3}:
            array = np.moveaxis(array, 0, -1)
        else:
            return None
    elif array.ndim != 2:
        return None
    array = _uint8_image_array(array)
    if array.ndim == 3 and array.shape[-1] == 1:
        return array[:, :, 0]
    return array


def _uint8_image_array(array: np.ndarray) -> np.ndarray:
    if np.issubdtype(array.dtype, np.floating):
        finite = array[np.isfinite(array)]
        if finite.size > 0 and float(finite.min()) >= 0.0 and float(finite.max()) <= 1.0:
            array = array * 255.0
    return np.clip(array, 0, 255).astype(np.uint8)


def _safe_filename(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    return safe or "image"


def _features(dataset: Any) -> dict[str, Any]:
    meta = getattr(dataset, "meta", None)
    return _dict_value(getattr(meta, "features", None) if meta is not None else None) or _dict_value(getattr(dataset, "features", None))


def _stats(dataset: Any) -> dict[str, Any]:
    meta = getattr(dataset, "meta", None)
    if meta is None:
        return {}
    return _dict_value(getattr(meta, "stats", None))


def _episode_metadata(dataset: Any, first_row: Mapping[str, Any] | None, episode_index: int) -> dict[str, Any]:
    metadata: dict[str, Any] = {"episode_index": episode_index}
    meta = getattr(dataset, "meta", None)
    for source in (getattr(meta, "episodes", None) if meta is not None else None, getattr(dataset, "episodes", None)):
        normalized = _normalize(source)
        if isinstance(normalized, Mapping):
            episode_data = normalized.get(episode_index) or normalized.get(str(episode_index))
            if isinstance(episode_data, Mapping):
                metadata.update(dict(episode_data))
    if first_row is not None:
        for key, value in first_row.items():
            if key.startswith("episode"):
                metadata[key] = _normalize(value)
    metadata["episode_index"] = episode_index
    return metadata


def _task_metadata(dataset: Any, first_row: Mapping[str, Any] | None) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if first_row is not None and "task" in first_row:
        metadata["task"] = _normalize(first_row["task"])
    meta = getattr(dataset, "meta", None)
    tasks = _normalize(getattr(meta, "tasks", None) if meta is not None else None)
    if tasks not in (None, {}):
        metadata["tasks"] = tasks
    return metadata


def _task_name(first_row: Mapping[str, Any] | None) -> str:
    if first_row is None or "task" not in first_row:
        return ""
    task = _normalize(first_row["task"])
    return task if isinstance(task, str) else ""


def _fps(dataset: Any) -> float:
    meta = getattr(dataset, "meta", None)
    fps = getattr(meta, "fps", None) if meta is not None else None
    if fps is None:
        fps = getattr(dataset, "fps", None)
    if fps is None:
        return 30.0
    try:
        return float(_scalar(fps))
    except (TypeError, ValueError):
        return 30.0


def _dict_value(value: Any) -> dict[str, Any]:
    normalized = _normalize(value)
    return dict(normalized) if isinstance(normalized, Mapping) else {}


def _first_value(row: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _int_value(value: Any, fallback: int) -> int:
    if value is None:
        return fallback
    try:
        return int(_scalar(value))
    except (TypeError, ValueError):
        return fallback


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(_scalar(value))
    except (TypeError, ValueError):
        return None


def _float_list(value: Any) -> list[float]:
    normalized = _normalize(value)
    if normalized is None:
        return []
    if isinstance(normalized, (int, float)):
        return [float(normalized)]
    if isinstance(normalized, list):
        return [float(item) for item in _flatten(normalized)]
    if isinstance(normalized, tuple):
        return [float(item) for item in _flatten(list(normalized))]
    return []


def _flatten(values: list[Any]) -> list[Any]:
    flattened: list[Any] = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(_flatten(value))
        else:
            flattened.append(value)
    return flattened


def _scalar(value: Any) -> Any:
    normalized = _normalize(value)
    if isinstance(normalized, list) and len(normalized) == 1:
        return normalized[0]
    return normalized


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool, Path)):
        return value
    for method in ("detach", "cpu", "numpy"):
        if hasattr(value, method):
            value = getattr(value, method)()
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    if hasattr(value, "tolist"):
        return _normalize(value.tolist())
    if isinstance(value, Mapping):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value
