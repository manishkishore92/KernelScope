from __future__ import annotations

import shutil
import subprocess
from typing import Any

from kernelscope.constants import TOOLCHAIN_TOOLS


def _version(command: str) -> str:
    try:
        result = subprocess.run([command, "--version"], capture_output=True, text=True, timeout=3)
        text = (result.stdout or result.stderr).strip().splitlines()
        return text[0] if text else "available"
    except Exception:
        return "available"


def check_toolchain(extra: list[str] | None = None) -> dict[str, Any]:
    tools = list(TOOLCHAIN_TOOLS)
    if extra:
        tools.extend(extra)
    seen = []
    output = []
    for tool in tools:
        if tool in seen:
            continue
        seen.append(tool)
        path = shutil.which(tool)
        output.append({
            "tool": tool,
            "found": bool(path),
            "path": path or "",
            "version": _version(tool) if path else "",
        })
    missing = [item["tool"] for item in output if not item["found"]]
    return {
        "tools": output,
        "found_count": len(output) - len(missing),
        "missing_count": len(missing),
        "missing": missing,
    }
