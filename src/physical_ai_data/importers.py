from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Mapping, Protocol


@dataclass(frozen=True)
class ImportRequest:
    source_format: str
    source: Mapping[str, object]
    output_dir: str | Path
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
    normalized_request = replace(request, output_dir=Path(request.output_dir))
    return importer.import_package(normalized_request)
