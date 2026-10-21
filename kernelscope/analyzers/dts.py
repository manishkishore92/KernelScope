from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import relative, require_path, walk_files

VENDOR_HINTS = {
    "qcom": ["qcom,", "qualcomm", "msm", "sdm", "sm"],
    "mediatek": ["mediatek", "mtk", "mt"],
    "exynos": ["samsung,exynos", "exynos"],
    "unisoc": ["sprd", "unisoc"],
}

DTS_KEYWORDS = [
    "reserved-memory",
    "firmware",
    "regulator",
    "gpio",
    "pinctrl",
    "qcom,msm-id",
    "chosen",
    "aliases",
    "thermal-zones",
    "memory@",
    "panel",
    "touchscreen",
]


def scan_dts(root: str | Path) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    files = list(walk_files(root_path, suffixes=[".dts", ".dtsi"]))
    vendor_counts = Counter()
    keyword_counts = Counter()
    examples = defaultdict(list)

    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")[:250_000].lower()
        rel = relative(path, root_path)
        for vendor, needles in VENDOR_HINTS.items():
            if any(needle in text or needle in rel.lower() for needle in needles):
                vendor_counts[vendor] += 1
                if len(examples[vendor]) < 8:
                    examples[vendor].append(rel)
        for keyword in DTS_KEYWORDS:
            if keyword.lower() in text:
                keyword_counts[keyword] += 1

    overlays = [relative(path, root_path) for path in files if "overlay" in str(path).lower() or path.name.endswith("-overlay.dts")]

    return {
        "root": str(root_path),
        "total_files": len(files),
        "dts_files": sum(1 for path in files if path.suffix == ".dts"),
        "dtsi_files": sum(1 for path in files if path.suffix == ".dtsi"),
        "vendor_hints": dict(vendor_counts),
        "vendor_examples": dict(examples),
        "keyword_counts": dict(keyword_counts),
        "overlay_candidates": overlays[:50],
    }
