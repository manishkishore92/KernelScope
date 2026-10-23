from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import relative, require_path, walk_files

MODULE_RE = re.compile(r"^\s*obj-(?:\$\((CONFIG_[A-Za-z0-9_]+)\)|[ym])\s*\+=\s*(.+)$")
CATEGORY_PATTERNS = {
    "camera": ["camera", "cam", "isp", "eeprom"],
    "audio": ["audio", "sound", "codec", "wcd", "snd"],
    "display": ["display", "gpu", "drm", "kgsl", "panel"],
    "wifi_bluetooth": ["wifi", "wlan", "bluetooth", "bt", "qca", "wcn"],
    "sensors": ["sensor", "imu", "gyro", "accelerometer", "magnetometer"],
    "fingerprint": ["fingerprint", "fpc", "goodix", "egis"],
    "power": ["power", "battery", "charger", "thermal", "bms"],
    "storage": ["ufs", "mmc", "sdhci", "storage"],
    "usb": ["usb", "typec", "dwc3"],
    "security": ["crypto", "tee", "qsee", "keymaster"],
}


def _category_for(text: str) -> str:
    lower = text.lower()
    for category, needles in CATEGORY_PATTERNS.items():
        if any(needle in lower for needle in needles):
            return category
    return "other"


def build_module_map(root: str | Path) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    built_modules: list[str] = []
    module_orders: list[str] = []
    symvers_files: list[str] = []
    entries: list[dict[str, Any]] = []
    categories: dict[str, list[str]] = defaultdict(list)
    module_out_candidates: list[str] = []
    vendor_module_paths: set[str] = set()

    for path in walk_files(root_path):
        rel = relative(path, root_path)
        lower = rel.lower()
        if path.suffix == ".ko":
            built_modules.append(rel)
            categories[_category_for(rel)].append(rel)
        elif path.name == "modules.order":
            module_orders.append(rel)
        elif path.name == "Module.symvers":
            symvers_files.append(rel)
        elif "module_out" in lower or "module_outs" in lower:
            module_out_candidates.append(rel)
        elif path.name in {"Makefile", "Kbuild"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = MODULE_RE.match(line)
                if not match:
                    continue
                targets = [part.strip() for part in match.group(2).split() if part.strip()]
                item = {
                    "file": rel,
                    "line": line_no,
                    "config": match.group(1) or "built-in rule",
                    "targets": targets,
                    "rule": line.strip(),
                    "category": _category_for(" ".join([rel, *targets])),
                }
                entries.append(item)
                if len(categories[item["category"]]) < 120:
                    categories[item["category"]].append(f"{rel}:{line_no}")
                if "vendor" in lower or "dlkm" in lower:
                    vendor_module_paths.add(rel)

    findings = []
    if not built_modules and not entries:
        findings.append({
            "severity": "medium",
            "category": "Modules",
            "message": "No built modules or Kbuild module rules were detected.",
            "suggestion": "This may be a monolithic kernel tree, but verify vendor module requirements for Android devices.",
        })
    if entries and not symvers_files:
        findings.append({
            "severity": "low",
            "category": "Module symbols",
            "message": "Module build rules exist, but no Module.symvers files were found in the tree/output.",
            "suggestion": "This is normal before a build. After building, review symbol exports if modules fail to load.",
        })

    return {
        "root": str(root_path),
        "built_module_count": len(built_modules),
        "kbuild_entry_count": len(entries),
        "module_order_files": sorted(module_orders)[:100],
        "module_symvers_files": sorted(symvers_files)[:100],
        "module_out_candidates": sorted(module_out_candidates)[:100],
        "vendor_module_paths": sorted(vendor_module_paths)[:100],
        "categories": {key: value[:80] for key, value in sorted(categories.items())},
        "kbuild_examples": entries[:120],
        "built_modules": sorted(built_modules)[:150],
        "findings": findings,
    }
