from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import relative, require_path, walk_files


HARDWARE_PATTERNS: dict[str, list[str]] = {
    "display": ["panel", "dsi", "display", "mdss", "drm"],
    "touchscreen": ["touchscreen", "touch", "synaptics", "goodix", "focaltech", "novatek"],
    "camera": ["camera", "camss", "cci", "csiphy", "eeprom"],
    "battery_charger": ["battery", "charger", "fuel-gauge", "bms", "smb", "qpnp-charger"],
    "regulators": ["regulator", "vreg", "ldo", "buck"],
    "gpio_pinctrl": ["gpio", "pinctrl", "tlmm"],
    "thermal": ["thermal-zones", "cooling-maps", "trip-point", "tsens"],
    "reserved_memory": ["reserved-memory", "memory-region", "qcom,ion"],
    "fingerprint": ["fingerprint", "fpc", "goodix_fp", "egis"],
    "audio": ["audio", "sound", "codec", "wcd", "speaker", "speaker-pa"],
    "wifi_bluetooth": ["wifi", "wlan", "bluetooth", "btfm", "qca", "wcn"],
    "gps": ["gps", "gnss"],
    "nfc": ["nfc", "pn553", "pn557", "st21"],
    "usb": ["usb", "typec", "dwc3", "tcpc"],
    "storage": ["ufs", "sdhci", "emmc", "mmc"],
}

SOC_HINTS = {
    "qualcomm": ["qcom,", "msm", "sdm", "sm", "kona", "lahaina", "bengal", "trinket", "atoll"],
    "mediatek": ["mediatek", "mtk", "mt6", "mt8"],
    "exynos": ["samsung,exynos", "exynos"],
    "unisoc": ["sprd", "unisoc", "ums"],
}


def build_dts_map(root: str | Path, sample_limit: int = 8) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    files = list(walk_files(root_path, suffixes=[".dts", ".dtsi"]))
    hardware: dict[str, dict[str, Any]] = {}
    soc_counts: dict[str, int] = {}
    examples: dict[str, list[str]] = defaultdict(list)

    for name in HARDWARE_PATTERNS:
        hardware[name] = {"detected": False, "count": 0, "examples": []}

    for path in files:
        rel = relative(path, root_path)
        lower_rel = rel.lower()
        text = path.read_text(encoding="utf-8", errors="ignore")[:500_000].lower()
        combined = lower_rel + "\n" + text
        for category, needles in HARDWARE_PATTERNS.items():
            if any(needle in combined for needle in needles):
                hardware[category]["detected"] = True
                hardware[category]["count"] += 1
                if len(hardware[category]["examples"]) < sample_limit:
                    hardware[category]["examples"].append(rel)
        for soc, needles in SOC_HINTS.items():
            if any(needle in combined for needle in needles):
                soc_counts[soc] = soc_counts.get(soc, 0) + 1
                if len(examples[soc]) < sample_limit:
                    examples[soc].append(rel)

    findings = []
    if not files:
        findings.append({
            "severity": "medium",
            "category": "DTS map",
            "message": "No DTS/DTSI files were detected.",
            "suggestion": "Confirm whether device trees are in a separate kernel/device repository.",
        })
    for category in ["display", "touchscreen", "camera", "battery_charger"]:
        if files and not hardware[category]["detected"]:
            findings.append({
                "severity": "low",
                "category": "Hardware hint",
                "message": f"No obvious {category.replace('_', ' ')} nodes were detected.",
                "suggestion": "This may be normal for shared SoC DTSI trees, but review board-specific DTS files.",
            })

    return {
        "root": str(root_path),
        "file_count": len(files),
        "dts_count": sum(1 for item in files if item.suffix == ".dts"),
        "dtsi_count": sum(1 for item in files if item.suffix == ".dtsi"),
        "hardware": hardware,
        "soc_hints": soc_counts,
        "soc_examples": dict(examples),
        "findings": findings,
    }
