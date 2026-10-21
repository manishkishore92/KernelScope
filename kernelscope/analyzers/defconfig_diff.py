from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.defconfig import parse_defconfig
from kernelscope.constants import ANDROID_KERNEL_CONFIGS, SECURITY_CONFIGS
from kernelscope.utils.filesystem import require_path


WATCHED = set(ANDROID_KERNEL_CONFIGS) | set(SECURITY_CONFIGS) | {
    "CONFIG_DEBUG_FS",
    "CONFIG_KPROBES",
    "CONFIG_KALLSYMS",
    "CONFIG_KALLSYMS_ALL",
    "CONFIG_DEVMEM",
    "CONFIG_MODULES",
    "CONFIG_MODULE_UNLOAD",
    "CONFIG_LTO_CLANG",
    "CONFIG_CFI_CLANG",
    "CONFIG_SHADOW_CALL_STACK",
}


def diff_defconfigs(old: str | Path, new: str | Path) -> dict[str, Any]:
    old_path = require_path(old, "old defconfig")
    new_path = require_path(new, "new defconfig")
    old_cfg = parse_defconfig(old_path)
    new_cfg = parse_defconfig(new_path)

    old_keys = set(old_cfg)
    new_keys = set(new_cfg)
    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed = sorted(key for key in old_keys & new_keys if old_cfg[key] != new_cfg[key])

    important = []
    for key in sorted((set(added) | set(removed) | set(changed)) & WATCHED):
        important.append({
            "config": key,
            "old": old_cfg.get(key, "missing"),
            "new": new_cfg.get(key, "missing"),
            "category": "security" if key in SECURITY_CONFIGS or key in {"CONFIG_DEBUG_FS", "CONFIG_KPROBES", "CONFIG_DEVMEM"} else "android",
        })

    findings = []
    for item in important:
        key = item["config"]
        old_value = item["old"]
        new_value = item["new"]
        if key in {"CONFIG_SECURITY_SELINUX", "CONFIG_SECURITY", "CONFIG_DM_VERITY"} and new_value in {"missing", "not set", "n"}:
            findings.append({
                "severity": "medium",
                "category": "Security regression",
                "message": f"{key} changed from {old_value} to {new_value}.",
                "suggestion": "Review this change before shipping an Android kernel build.",
            })
        if key in {"CONFIG_DEBUG_FS", "CONFIG_KPROBES", "CONFIG_DEVMEM"} and new_value == "y":
            findings.append({
                "severity": "low",
                "category": "Debug config",
                "message": f"{key} is enabled in the new defconfig.",
                "suggestion": "Confirm debug capabilities are intended for this build type.",
            })
        if key == "CONFIG_MODULE_SIG" and new_value in {"missing", "not set", "n"}:
            findings.append({
                "severity": "low",
                "category": "Module signing",
                "message": "Kernel module signature support is not enabled in the new defconfig.",
                "suggestion": "Review module signing requirements for this device and ROM branch.",
            })

    return {
        "old": str(old_path),
        "new": str(new_path),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "added": added[:300],
        "removed": removed[:300],
        "changed": [{"config": key, "old": old_cfg[key], "new": new_cfg[key]} for key in changed[:300]],
        "important_changes": important,
        "findings": findings,
    }
