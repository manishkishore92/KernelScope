from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from kernelscope.analyzers.scanner import find_defconfigs
from kernelscope.analyzers.security import evaluate_config
from kernelscope.utils.filesystem import relative, require_path

CONFIG_RE = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$")
NOT_SET_RE = re.compile(r"^#\s*(CONFIG_[A-Za-z0-9_]+)\s+is not set")


def parse_defconfig(path: str | Path) -> dict[str, str]:
    p = require_path(path, "defconfig")
    config: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        match = CONFIG_RE.match(stripped)
        if match:
            config[match.group(1)] = match.group(2).strip().strip('"')
            continue
        match = NOT_SET_RE.match(stripped)
        if match:
            config[match.group(1)] = "not set"
    return config


def inspect_defconfig(path: str | Path) -> dict[str, Any]:
    p = require_path(path, "defconfig")
    config = parse_defconfig(p)
    enabled = sum(1 for value in config.values() if value == "y")
    modules = sum(1 for value in config.values() if value == "m")
    not_set = sum(1 for value in config.values() if value == "not set")
    values = len(config) - enabled - modules - not_set
    security = evaluate_config(config)
    return {
        "path": str(p),
        "name": p.name,
        "option_count": len(config),
        "enabled": enabled,
        "modules": modules,
        "not_set": not_set,
        "values": values,
        "android_options": security["android"],
        "security_options": security["security"],
        "findings": security["findings"],
    }


def inspect_tree_defconfigs(root: str | Path, limit: int = 20) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    configs = find_defconfigs(root_path)
    inspected = []
    for rel in configs[:limit]:
        inspected.append(inspect_defconfig(root_path / rel))
    return {
        "root": str(root_path),
        "total_defconfigs": len(configs),
        "inspected_count": len(inspected),
        "defconfigs": [{**item, "path": relative(item["path"], root_path)} for item in inspected],
    }
