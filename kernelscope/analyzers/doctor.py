from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.anykernel import inspect_anykernel
from kernelscope.analyzers.defconfig import inspect_tree_defconfigs
from kernelscope.analyzers.dts import scan_dts
from kernelscope.analyzers.modules import scan_modules
from kernelscope.analyzers.scanner import scan_tree
from kernelscope.analyzers.toolchain import check_toolchain


def _finding(severity: str, category: str, message: str, suggestion: str = "") -> dict[str, str]:
    return {"severity": severity, "category": category, "message": message, "suggestion": suggestion}


def run_doctor(root: str | Path) -> dict[str, Any]:
    tree = scan_tree(root)
    defconfigs = inspect_tree_defconfigs(root, limit=3)
    dts = scan_dts(root)
    modules = scan_modules(root)
    toolchain = check_toolchain()
    anykernel = inspect_anykernel(root)

    findings: list[dict[str, str]] = []
    findings.extend(tree.get("findings", []))

    if tree["kernel_version"] == "Unknown":
        findings.append(_finding("medium", "Kernel version", "Kernel version could not be parsed from the top-level Makefile.", "Confirm this is a complete kernel source tree."))
    if tree["defconfig_count"] == 0:
        findings.append(_finding("high", "Defconfig", "No defconfig files were found.", "Add or locate the device defconfig under arch/<arch>/configs."))
    if dts["total_files"] == 0:
        findings.append(_finding("medium", "DTS", "No DTS/DTSI files were found.", "Confirm whether the device tree sources are stored in a separate repository."))
    if not anykernel["detected"]:
        findings.append(_finding("low", "Packaging", "AnyKernel3 packaging files were not detected.", "This is optional, but useful for kernel ZIP release workflows."))
    if toolchain["missing_count"] > 0:
        findings.append(_finding("medium", "Toolchain", f"Missing tools: {', '.join(toolchain['missing'][:8])}", "Install missing build dependencies before starting a kernel build."))

    for item in defconfigs.get("defconfigs", []):
        findings.extend(item.get("findings", []))

    score = 100
    for item in findings:
        severity = item.get("severity", "low")
        if severity == "high":
            score -= 14
        elif severity == "medium":
            score -= 7
        else:
            score -= 3
    score = max(0, min(100, score))

    return {
        "root": str(Path(root).expanduser().resolve()),
        "score": score,
        "summary": {
            "kernel_version": tree["kernel_version"],
            "arches": tree["arches"],
            "defconfigs": tree["defconfig_count"],
            "dts_files": dts["dts_files"],
            "dtsi_files": dts["dtsi_files"],
            "module_entries": modules["kbuild_entry_count"],
            "anykernel": anykernel["detected"],
            "missing_tools": toolchain["missing_count"],
        },
        "findings": findings,
        "tree": tree,
        "defconfigs": defconfigs,
        "dts": dts,
        "modules": modules,
        "toolchain": toolchain,
        "anykernel": anykernel,
    }
