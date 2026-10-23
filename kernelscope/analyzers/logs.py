from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.constants import LOG_PATTERNS
from kernelscope.utils.filesystem import require_path


def analyze_log(path: str | Path, context: int = 1) -> dict[str, Any]:
    log_path = require_path(path, "build log")
    lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    findings = []
    for index, line in enumerate(lines):
        lower = line.lower()
        for pattern in LOG_PATTERNS:
            if any(needle.lower() in lower for needle in pattern["needles"]):
                start = max(0, index - context)
                end = min(len(lines), index + context + 1)
                findings.append({
                    "severity": pattern["severity"],
                    "category": pattern["category"],
                    "line": index + 1,
                    "matched": line.strip(),
                    "context": lines[start:end],
                    "suggestion": pattern["suggestion"],
                })
                break
    categories: dict[str, int] = {}
    for item in findings:
        categories[item["category"]] = categories.get(item["category"], 0) + 1
    return {
        "path": str(log_path),
        "line_count": len(lines),
        "finding_count": len(findings),
        "categories": categories,
        "findings": findings[:200],
    }
