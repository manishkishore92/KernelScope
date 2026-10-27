from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import relative, require_path, walk_files

EXPORT_RE = re.compile(r"\bEXPORT_SYMBOL(?:_GPL|_NS|_GPL_FUTURE)?\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)")
SYMVERS_NAMES = {"Module.symvers", "vmlinux.symvers"}
KMI_NAME_HINTS = ("abi", "kmi", "symbol")
SOURCE_SUFFIXES = {".c", ".h", ".S", ".s"}


def _read_limited(path: Path, limit: int = 2_000_000) -> str:
    try:
        if path.stat().st_size > limit:
            return path.read_text(encoding="utf-8", errors="ignore")[:limit]
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _parse_symvers(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in _read_limited(path, limit=6_000_000).splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0].startswith("0x"):
            rows.append({"crc": parts[0], "symbol": parts[1], "module": parts[2], "export_type": parts[3]})
    return rows


def scan_symbols(root: str | Path) -> dict[str, Any]:
    """Inspect exported symbols, Module.symvers files, and KMI/ABI symbol lists."""
    root_path = require_path(root, "kernel tree")
    symvers_files: list[Path] = []
    kmi_files: list[Path] = []
    export_counter: Counter[str] = Counter()
    export_files: dict[str, list[str]] = defaultdict(list)
    source_files_scanned = 0

    for file in walk_files(root_path):
        rel = relative(file, root_path)
        lower_name = file.name.lower()
        lower_rel = rel.lower()
        if file.name in SYMVERS_NAMES:
            symvers_files.append(file)
        if any(hint in lower_name for hint in KMI_NAME_HINTS) and any(token in lower_rel for token in ["android/abi", "abi_gki", "kmi", "symbols"]):
            if file.is_file() and file.suffix.lower() not in {".o", ".ko", ".cmd"}:
                kmi_files.append(file)
        if file.suffix in SOURCE_SUFFIXES:
            text = _read_limited(file)
            if text:
                source_files_scanned += 1
            for match in EXPORT_RE.finditer(text):
                symbol = match.group(1)
                export_counter[symbol] += 1
                if len(export_files[symbol]) < 8:
                    export_files[symbol].append(rel)

    symvers_rows: list[dict[str, str]] = []
    for item in symvers_files[:12]:
        symvers_rows.extend(_parse_symvers(item))

    duplicate_exports = [
        {"symbol": symbol, "count": count, "files": export_files.get(symbol, [])}
        for symbol, count in export_counter.most_common()
        if count > 1
    ][:80]

    modules = Counter(row.get("module", "") for row in symvers_rows if row.get("module"))
    export_types = Counter(row.get("export_type", "") for row in symvers_rows if row.get("export_type"))

    findings: list[dict[str, Any]] = []
    if not symvers_files:
        findings.append({
            "severity": "low",
            "category": "Symbols",
            "message": "No Module.symvers or vmlinux.symvers file was detected.",
            "suggestion": "Run a kernel build first if you need a complete symbol/module compatibility report.",
        })
    if not kmi_files:
        findings.append({
            "severity": "low",
            "category": "KMI",
            "message": "No obvious ABI/KMI symbol list was detected.",
            "suggestion": "For GKI-style kernels, review android/abi or vendor ABI symbol list handling before changing exported symbols.",
        })
    if duplicate_exports:
        findings.append({
            "severity": "medium",
            "category": "Symbols",
            "message": f"{len(duplicate_exports)} exported symbol names appear more than once.",
            "suggestion": "Review duplicate exports before rebasing or mixing vendor driver trees.",
        })
    if source_files_scanned == 0:
        findings.append({
            "severity": "high",
            "category": "Source",
            "message": "No kernel source files were scanned for exported symbols.",
            "suggestion": "Confirm this path points to a kernel source tree, not only build output or packaging files.",
        })

    return {
        "root": str(root_path),
        "source_files_scanned": source_files_scanned,
        "symvers_files": [relative(path, root_path) for path in sorted(symvers_files)[:80]],
        "symvers_file_count": len(symvers_files),
        "symvers_symbol_count": len(symvers_rows),
        "top_symvers_modules": [{"module": mod, "count": count} for mod, count in modules.most_common(20)],
        "export_types": dict(export_types),
        "exported_symbol_count": sum(export_counter.values()),
        "unique_exported_symbol_count": len(export_counter),
        "top_exported_symbols": [{"symbol": sym, "count": count, "files": export_files.get(sym, [])} for sym, count in export_counter.most_common(25)],
        "duplicate_exports": duplicate_exports,
        "kmi_files": [relative(path, root_path) for path in sorted(set(kmi_files))[:100]],
        "kmi_file_count": len(set(kmi_files)),
        "findings": findings,
    }
