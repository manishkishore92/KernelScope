from __future__ import annotations

from collections import Counter
from typing import Any


def normalize_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, Any]] = []
    rank = {"high": 0, "medium": 1, "low": 2, "info": 3}
    for item in sorted(findings, key=lambda x: rank.get(str(x.get("severity", "low")), 2)):
        key = (str(item.get("severity", "low")), str(item.get("category", "")), str(item.get("message", "")))
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def build_recommendation_plan(data: dict[str, Any]) -> dict[str, Any]:
    findings = normalize_findings(data.get("findings", []))
    by_severity = Counter(str(item.get("severity", "low")) for item in findings)
    by_category = Counter(str(item.get("category", "General")) for item in findings)

    immediate: list[str] = []
    before_build: list[str] = []
    before_release: list[str] = []
    automation: list[str] = []

    scan = data.get("scan", {})
    build_system = data.get("build_system", {})
    package = data.get("package", {})
    gki = data.get("gki", {})
    security = data.get("security", {})
    symbols = data.get("symbols", {})

    if scan.get("kernel_version") in {None, "Unknown"}:
        immediate.append("Confirm the selected directory is the actual kernel source root and contains a readable top-level Makefile.")
    if scan.get("defconfig_count", 0) == 0:
        immediate.append("Locate or add the device defconfig under arch/<arch>/configs before creating a repeatable build command.")
    if build_system.get("primary") == "Unknown":
        immediate.append("Identify the build entrypoint: Makefile, Android build.config/build.sh, or Kleaf/Bazel.")
    if not build_system.get("systems"):
        before_build.append("Add or document the build path used by this kernel tree so other maintainers can reproduce builds.")
    if gki.get("gki_detected") and not gki.get("kmi_symbol_lists_detected"):
        before_build.append("Review ABI/KMI symbol list handling because this tree has GKI hints but no obvious symbol list.")
    if security.get("findings"):
        before_release.append("Review Android/security defconfig findings and keep release-specific debug options intentional.")
    if symbols.get("duplicate_exports"):
        before_release.append("Review duplicate exported symbols before rebasing vendor drivers or publishing a kernel package.")
    if not package.get("ready"):
        before_release.append("Run the package checker against the final AnyKernel3/output folder before release.")

    automation.extend([
        "Generate an intelligence report before major rebases.",
        "Analyze failed build logs with kernelscope analyze-log before making manual changes.",
        "Use diff-defconfig when changing release or device defconfigs.",
    ])

    if not immediate:
        immediate.append("Run a clean kernel build and save the full log for analysis if it fails.")
    if not before_build:
        before_build.append("Confirm ARCH, defconfig, compiler, output directory, and expected image path in the generated build plan.")
    if not before_release:
        before_release.append("Generate release notes, checksums, and package audit output before publishing a kernel ZIP.")

    return {
        "summary": {
            "finding_count": len(findings),
            "by_severity": dict(by_severity),
            "top_categories": [{"category": cat, "count": count} for cat, count in by_category.most_common(12)],
        },
        "immediate": immediate,
        "before_build": before_build,
        "before_release": before_release,
        "automation": automation,
        "findings": findings,
    }
