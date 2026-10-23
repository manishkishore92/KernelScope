from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.anykernel import inspect_anykernel
from kernelscope.analyzers.build_system import detect_build_system
from kernelscope.analyzers.defconfig import inspect_tree_defconfigs
from kernelscope.analyzers.doctor import run_doctor
from kernelscope.analyzers.dts_map import build_dts_map
from kernelscope.analyzers.gki import check_gki
from kernelscope.analyzers.module_map import build_module_map
from kernelscope.analyzers.package_checker import check_package
from kernelscope.analyzers.scanner import scan_tree
from kernelscope.analyzers.security_audit import run_security_audit
from kernelscope.analyzers.symbols import scan_symbols
from kernelscope.analyzers.toolchain import check_toolchain
from kernelscope.utils.filesystem import require_path


def _score_category(ok: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, round((ok / total) * 100)))


def readiness_breakdown(data: dict[str, Any]) -> dict[str, Any]:
    tree = data["scan"]
    gki = data["gki"]
    dts = data["dts_map"]
    modules = data["modules"]
    build_system = data["build_system"]
    security = data["security"]
    toolchain = data["toolchain"]
    package = data["package"]
    symbols = data.get("symbols", {})

    categories = {
        "kernel_structure": 20 if tree.get("kernel_version") != "Unknown" and tree.get("arches") else 10 if tree.get("arches") else 0,
        "defconfigs": 15 if tree.get("defconfig_count", 0) > 0 else 0,
        "dts_sources": 15 if dts.get("file_count", 0) > 0 else 0,
        "modules": 10 if modules.get("kbuild_entry_count", 0) or modules.get("built_module_count", 0) else 4,
        "build_system": 15 if build_system.get("primary") != "Unknown" else 0,
        "security_review": 10 if security.get("inspected_count", 0) else 0,
        "toolchain": 10 if toolchain.get("missing_count", 0) == 0 else max(0, 10 - min(10, toolchain.get("missing_count", 0))),
        "packaging": 5 if package.get("ready") else 2,
        "symbols": 5 if symbols.get("unique_exported_symbol_count", 0) or symbols.get("symvers_symbol_count", 0) else 1,
    }
    score = sum(categories.values())
    if gki.get("gki_detected"):
        score += 5 if gki.get("kmi_symbol_lists_detected") else 2
    score = max(0, min(100, score))
    return {"score": score, "categories": categories}


def collect_findings(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for section in sections:
        for item in section.get("findings", []):
            findings.append(item)
    # Keep stable order by severity importance while preserving category detail.
    rank = {"high": 0, "medium": 1, "low": 2, "info": 3}
    return sorted(findings, key=lambda item: rank.get(str(item.get("severity", "low")), 2))


def run_intelligence(root: str | Path) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    scan = scan_tree(root_path)
    doctor = run_doctor(root_path)
    defconfigs = inspect_tree_defconfigs(root_path, limit=8)
    dts_map = build_dts_map(root_path)
    modules = build_module_map(root_path)
    build_system = detect_build_system(root_path)
    gki = check_gki(root_path)
    security = run_security_audit(root_path, limit=8)
    toolchain = check_toolchain()
    anykernel = inspect_anykernel(root_path)
    package = check_package(root_path)
    symbols = scan_symbols(root_path)

    data = {
        "root": str(root_path),
        "scan": scan,
        "doctor": doctor,
        "defconfigs": defconfigs,
        "dts_map": dts_map,
        "modules": modules,
        "build_system": build_system,
        "gki": gki,
        "security": security,
        "toolchain": toolchain,
        "anykernel": anykernel,
        "package": package,
        "symbols": symbols,
    }
    data["readiness"] = readiness_breakdown(data)
    data["findings"] = collect_findings(doctor, dts_map, modules, build_system, gki, security, package, symbols)
    data["next_steps"] = suggest_next_steps(data)
    return data


def suggest_next_steps(data: dict[str, Any]) -> list[str]:
    steps: list[str] = []
    scan = data["scan"]
    if scan.get("defconfig_count", 0) == 0:
        steps.append("Locate or create the device defconfig under arch/<arch>/configs before building.")
    if data["build_system"].get("primary") == "Unknown":
        steps.append("Confirm the kernel build entrypoint: Kleaf/Bazel, build.config/build.sh, or a normal Makefile build.")
    if data["dts_map"].get("file_count", 0) == 0:
        steps.append("Find the board DTS/DTSI sources or confirm they are stored in a separate repository.")
    if data["toolchain"].get("missing_count", 0):
        missing = ", ".join(data["toolchain"].get("missing", [])[:6])
        steps.append(f"Install missing build tools before compiling: {missing}.")
    if data["gki"].get("gki_detected") and not data["gki"].get("kmi_symbol_lists_detected"):
        steps.append("Review KMI/ABI symbol list handling before changing exported symbols.")
    if data.get("symbols", {}).get("duplicate_exports"):
        steps.append("Review duplicate exported symbols before shipping or rebasing vendor driver changes.")
    if not data["package"].get("image_files"):
        steps.append("After a successful build, copy kernel image outputs into the selected packaging workflow.")
    if not steps:
        steps.append("Run a real kernel build and analyze the build log with kernelscope analyze-log if it fails.")
    return steps
