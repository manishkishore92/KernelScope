from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from kernelscope.models import Finding
from kernelscope.utils.filesystem import find_by_name, relative, require_path, walk_files


def read_kernel_version(root: str | Path) -> str:
    root_path = require_path(root, "kernel tree")
    makefile = root_path / "Makefile"
    if not makefile.exists():
        return "Unknown"
    values: dict[str, str] = {}
    pattern = re.compile(r"^(VERSION|PATCHLEVEL|SUBLEVEL|EXTRAVERSION)\s*=\s*(.*)$")
    for line in makefile.read_text(encoding="utf-8", errors="ignore").splitlines()[:80]:
        match = pattern.match(line.strip())
        if match:
            values[match.group(1)] = match.group(2).strip()
    if not values:
        return "Unknown"
    base = ".".join([values.get("VERSION", "0"), values.get("PATCHLEVEL", "0"), values.get("SUBLEVEL", "0")])
    return f"{base}{values.get('EXTRAVERSION', '')}"


def detect_arches(root: str | Path) -> list[str]:
    arch_dir = Path(root) / "arch"
    if not arch_dir.exists():
        return []
    return sorted([path.name for path in arch_dir.iterdir() if path.is_dir() and not path.name.startswith(".")])


def find_defconfigs(root: str | Path) -> list[str]:
    root_path = require_path(root, "kernel tree")
    configs: list[str] = []
    arch_dir = root_path / "arch"
    if arch_dir.exists():
        for path in arch_dir.glob("*/configs/*defconfig"):
            if path.is_file():
                configs.append(relative(path, root_path))
    return sorted(configs)


def scan_android_files(root: str | Path) -> dict[str, list[str]]:
    root_path = require_path(root, "kernel tree")
    groups = {
        "build_configs": [],
        "android_makefiles": [],
        "module_files": [],
        "known_outputs": [],
    }
    for path in walk_files(root_path):
        rel = relative(path, root_path)
        name = path.name
        if name.startswith("build.config"):
            groups["build_configs"].append(rel)
        elif name in {"Android.bp", "Android.mk"}:
            groups["android_makefiles"].append(rel)
        elif name in {"modules.order", "Module.symvers"} or name.endswith(".ko"):
            groups["module_files"].append(rel)
        elif name in {"Image", "Image.gz", "Image.gz-dtb", "dtbo.img", "vendor_boot.img"}:
            groups["known_outputs"].append(rel)
    return {key: sorted(value) for key, value in groups.items()}


def scan_tree(root: str | Path) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    findings: list[Finding] = []
    if not (root_path / "Makefile").exists():
        findings.append(Finding("high", "Structure", "Top-level Makefile was not found.", "Run KernelScope from the root of a Linux/Android kernel source tree."))
    if not (root_path / "arch").exists():
        findings.append(Finding("high", "Structure", "arch/ directory was not found.", "Verify that the selected path is a kernel source tree."))

    dts_count = 0
    dtsi_count = 0
    module_count = 0
    for path in walk_files(root_path, suffixes=[".dts", ".dtsi", ".ko"]):
        if path.suffix == ".dts":
            dts_count += 1
        elif path.suffix == ".dtsi":
            dtsi_count += 1
        elif path.suffix == ".ko":
            module_count += 1

    anykernel_files = find_by_name(root_path, ["anykernel.sh", "ak3-core.sh"])
    android_files = scan_android_files(root_path)
    defconfigs = find_defconfigs(root_path)
    arches = detect_arches(root_path)

    if not defconfigs:
        findings.append(Finding("medium", "Defconfig", "No defconfig files found under arch/*/configs.", "Check whether this kernel tree stores defconfigs in a device-specific path."))
    if dts_count == 0 and dtsi_count == 0:
        findings.append(Finding("medium", "DTS", "No DTS/DTSI files found.", "Some common kernels store device trees outside the main tree; verify the source layout."))

    return {
        "path": str(root_path),
        "kernel_version": read_kernel_version(root_path),
        "arches": arches,
        "defconfigs": defconfigs,
        "defconfig_count": len(defconfigs),
        "dts_count": dts_count,
        "dtsi_count": dtsi_count,
        "module_count": module_count,
        "anykernel_detected": bool(anykernel_files),
        "anykernel_files": [relative(path, root_path) for path in anykernel_files],
        "android_files": android_files,
        "findings": [item.to_dict() for item in findings],
    }
