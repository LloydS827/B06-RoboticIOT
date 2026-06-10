from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol


@dataclass(frozen=True)
class ImportRequest:
    source_format: str
    source: Mapping[str, object]
    output_dir: Path
    options: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ImportResult:
    package_root: Path
    source_format: str
    source_id: str
    frame_count: int
    warnings: list[str] = field(default_factory=list)


class PackageImporter(Protocol):
    source_format: str

    def import_package(self, request: ImportRequest) -> ImportResult:
        ...


def run_import(importer: PackageImporter, request: ImportRequest) -> ImportResult:
    if importer.source_format != request.source_format:
        raise ValueError(f"Importer source_format {importer.source_format} cannot handle {request.source_format}")
    return importer.import_package(request)
