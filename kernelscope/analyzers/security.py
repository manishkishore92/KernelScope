from __future__ import annotations

from typing import Any

from kernelscope.constants import ANDROID_KERNEL_CONFIGS, SECURITY_CONFIGS


def evaluate_config(config: dict[str, str]) -> dict[str, Any]:
    android = {}
    security = {}
    findings = []

    for key, description in ANDROID_KERNEL_CONFIGS.items():
        value = config.get(key, "missing")
        android[key] = {"description": description, "value": value}
        if value == "missing" and key in {"CONFIG_ANDROID_BINDER_IPC", "CONFIG_CGROUPS"}:
            findings.append({
                "severity": "medium",
                "category": "Android config",
                "message": f"{key} is not present in the defconfig.",
                "suggestion": "Confirm this option is enabled through another fragment or generated config before building Android userspace.",
            })

    for key, description in SECURITY_CONFIGS.items():
        value = config.get(key, "missing")
        security[key] = {"description": description, "value": value}
        if key in {"CONFIG_SECURITY_SELINUX", "CONFIG_STRICT_KERNEL_RWX"} and value not in {"y", "m"}:
            findings.append({
                "severity": "medium",
                "category": "Security config",
                "message": f"{key} is not enabled in this defconfig.",
                "suggestion": "Review ROM and device requirements before changing security-related options.",
            })

    return {"android": android, "security": security, "findings": findings}
