from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import relative, require_path, walk_files


KLEAF_MARKERS = {
    "MODULE.bazel",
    "MODULE.bazel.lock",
    "WORKSPACE",
    "WORKSPACE.bazel",
    "BUILD.bazel",
    "BUILD",
}
LEGACY_MARKERS = {
    "build.sh",
    "build.config",
}


def detect_build_system(root: str | Path) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    build_configs: list[str] = []
    bazel_files: list[str] = []
    build_scripts: list[str] = []
    makefiles: list[str] = []
    android_files: list[str] = []
    anykernel_files: list[str] = []
    custom_scripts: list[str] = []

    for path in walk_files(root_path):
        rel = relative(path, root_path)
        name = path.name
        if name.startswith("build.config"):
            build_configs.append(rel)
        if name in KLEAF_MARKERS or name.endswith(".bzl") or "kleaf" in rel.lower():
            bazel_files.append(rel)
        if name == "build.sh" or name.endswith("_build.sh"):
            build_scripts.append(rel)
        if name == "Makefile":
            makefiles.append(rel)
        if name in {"Android.bp", "Android.mk"}:
            android_files.append(rel)
        if name in {"anykernel.sh", "ak3-core.sh"}:
            anykernel_files.append(rel)
        if path.suffix == ".sh" and any(token in name.lower() for token in ["build", "kernel", "compile", "make"]):
            custom_scripts.append(rel)

    systems: list[str] = []
    if bazel_files:
        systems.append("Kleaf / Bazel")
    if build_configs or build_scripts:
        systems.append("Android build.config / build.sh")
    if (root_path / "Makefile").exists():
        systems.append("Makefile")
    if anykernel_files:
        systems.append("AnyKernel3 packaging")
    if custom_scripts:
        systems.append("Custom shell scripts")

    primary = systems[0] if systems else "Unknown"
    findings = []
    if primary == "Unknown":
        findings.append({
            "severity": "high",
            "category": "Build system",
            "message": "No recognizable kernel build system files were detected.",
            "suggestion": "Check whether this is the root of the kernel source tree or whether build files are stored in a separate manifest project.",
        })
    if bazel_files and build_configs:
        findings.append({
            "severity": "low",
            "category": "Build system",
            "message": "Both Kleaf/Bazel and legacy build.config files were detected.",
            "suggestion": "Confirm which build path is used for this device before generating a build script.",
        })
    if not anykernel_files:
        findings.append({
            "severity": "low",
            "category": "Packaging",
            "message": "AnyKernel3 packaging files were not detected in this tree.",
            "suggestion": "This is optional, but useful when publishing standalone kernel ZIPs.",
        })

    return {
        "root": str(root_path),
        "primary": primary,
        "systems": systems,
        "bazel_files": sorted(bazel_files)[:120],
        "build_configs": sorted(build_configs)[:120],
        "build_scripts": sorted(build_scripts)[:80],
        "makefiles": sorted(makefiles)[:80],
        "android_files": sorted(android_files)[:80],
        "anykernel_files": sorted(anykernel_files)[:50],
        "custom_scripts": sorted(custom_scripts)[:80],
        "findings": findings,
    }
