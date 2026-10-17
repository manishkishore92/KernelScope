from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from kernelscope.constants import IGNORED_DIRS


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def require_path(path: str | Path, expected: str = "path") -> Path:
    resolved = resolve_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"{expected} does not exist: {resolved}")
    return resolved


def walk_files(root: str | Path, suffixes: Sequence[str] | None = None) -> Iterator[Path]:
    root_path = require_path(root, "root")
    suffixes_lower = tuple(s.lower() for s in suffixes) if suffixes else None
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for filename in filenames:
            path = Path(dirpath) / filename
            if suffixes_lower and path.suffix.lower() not in suffixes_lower:
                continue
            yield path


def find_by_name(root: str | Path, names: Iterable[str]) -> list[Path]:
    name_set = set(names)
    return [path for path in walk_files(root) if path.name in name_set]


def find_by_suffix(root: str | Path, suffixes: Sequence[str]) -> list[Path]:
    return list(walk_files(root, suffixes=suffixes))


def relative(path: str | Path, root: str | Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except Exception:
        return str(path)


def read_text(path: str | Path, limit: int | None = None) -> str:
    p = Path(path)
    data = p.read_text(encoding="utf-8", errors="ignore")
    if limit is not None:
        return data[:limit]
    return data


def write_text(path: str | Path, content: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def file_size(path: str | Path) -> int:
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0
