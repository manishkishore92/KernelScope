from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.scanner import scan_tree


def compare_trees(old: str | Path, new: str | Path) -> dict[str, Any]:
    old_scan = scan_tree(old)
    new_scan = scan_tree(new)
    old_defs = set(old_scan.get("defconfigs", []))
    new_defs = set(new_scan.get("defconfigs", []))
    return {
        "old": old_scan["path"],
        "new": new_scan["path"],
        "kernel_version": {"old": old_scan["kernel_version"], "new": new_scan["kernel_version"], "changed": old_scan["kernel_version"] != new_scan["kernel_version"]},
        "defconfigs_added": sorted(new_defs - old_defs),
        "defconfigs_removed": sorted(old_defs - new_defs),
        "counts": {
            "old_defconfigs": old_scan["defconfig_count"],
            "new_defconfigs": new_scan["defconfig_count"],
            "old_dts": old_scan["dts_count"],
            "new_dts": new_scan["dts_count"],
            "old_dtsi": old_scan["dtsi_count"],
            "new_dtsi": new_scan["dtsi_count"],
        },
    }
