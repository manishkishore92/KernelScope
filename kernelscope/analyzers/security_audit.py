from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.defconfig import inspect_defconfig
from kernelscope.analyzers.scanner import find_defconfigs
from kernelscope.constants import SECURITY_CONFIGS
from kernelscope.utils.filesystem import relative, require_path


SECURITY_EXPECTATIONS = {
    "CONFIG_SECURITY": "y",
    "CONFIG_SECURITY_SELINUX": "y",
    "CONFIG_DM_VERITY": "y",
    "CONFIG_STRICT_KERNEL_RWX": "y",
    "CONFIG_STRICT_MODULE_RWX": "y",
    "CONFIG_RANDOMIZE_BASE": "y",
    "CONFIG_STACKPROTECTOR_STRONG": "y",
    "CONFIG_HARDENED_USERCOPY": "y",
    "CONFIG_FORTIFY_SOURCE": "y",
}

REVIEW_CONFIGS = {
    "CONFIG_DEBUG_FS": "Debug filesystem is useful for development but should be reviewed for release builds.",
    "CONFIG_KPROBES": "Kprobes can be useful for debugging and instrumentation; review release policy.",
    "CONFIG_DEVMEM": "Direct physical memory access should be reviewed carefully.",
    "CONFIG_KALLSYMS_ALL": "Full symbol exposure can help debugging but may be undesirable for public builds.",
    "CONFIG_MODULE_SIG": "Module signing may be required by some workflows.",
    "CONFIG_MODULE_SIG_FORCE": "Forced module signing can affect third-party module loading.",
}


def run_security_audit(root: str | Path, limit: int = 8) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    defconfigs = find_defconfigs(root_path)
    inspected = []
    findings = []
    aggregate: dict[str, dict[str, int]] = {}

    for rel in defconfigs[:limit]:
        info = inspect_defconfig(root_path / rel)
        inspected.append({"path": rel, "name": info["name"], "option_count": info["option_count"]})
        values = {**{key: item["value"] for key, item in info.get("security_options", {}).items()}}
        for key, expected in SECURITY_EXPECTATIONS.items():
            value = values.get(key, "missing")
            aggregate.setdefault(key, {})[value] = aggregate.setdefault(key, {}).get(value, 0) + 1
            if value not in {expected, "m"}:
                findings.append({
                    "severity": "medium",
                    "category": "Security config",
                    "message": f"{key} is {value} in {rel}.",
                    "suggestion": SECURITY_CONFIGS.get(key, "Review Android kernel security requirements."),
                    "file": rel,
                })
        raw = info.get("security_options", {})
        raw.update(info.get("android_options", {}))
        # Re-parse value map from the full defconfig through inspect output where available.
        for key, note in REVIEW_CONFIGS.items():
            value = "missing"
            for group in [info.get("security_options", {}), info.get("android_options", {})]:
                if key in group:
                    value = group[key].get("value", "missing")
            if key in {"CONFIG_DEBUG_FS", "CONFIG_KPROBES", "CONFIG_DEVMEM", "CONFIG_KALLSYMS_ALL"} and value == "y":
                findings.append({
                    "severity": "low",
                    "category": "Review config",
                    "message": f"{key} is enabled in {rel}.",
                    "suggestion": note,
                    "file": rel,
                })

    if not defconfigs:
        findings.append({
            "severity": "high",
            "category": "Security audit",
            "message": "No defconfig files were found for security analysis.",
            "suggestion": "Locate the device defconfig or generate a merged .config before review.",
        })

    return {
        "root": str(root_path),
        "defconfig_count": len(defconfigs),
        "inspected_count": len(inspected),
        "inspected": inspected,
        "aggregate": aggregate,
        "findings": findings[:200],
    }
