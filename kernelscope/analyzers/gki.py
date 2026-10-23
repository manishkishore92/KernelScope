from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import relative, require_path, walk_files


ABI_HINTS = ["abi", "kmi", "symbol_list", "protected_modules", "module_outs"]
GKI_HINTS = ["gki_defconfig", "android-base", "android-recommended", "build.config.gki", "common/android"]


def check_gki(root: str | Path) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    abi_files: list[str] = []
    kmi_symbol_lists: list[str] = []
    protected_modules: list[str] = []
    gki_files: list[str] = []
    module_outs_files: list[str] = []
    vendor_module_dirs: set[str] = set()

    for path in walk_files(root_path):
        rel = relative(path, root_path)
        lower = rel.lower()
        name = path.name.lower()
        if any(hint in lower for hint in ABI_HINTS):
            abi_files.append(rel)
        if "abi_gki" in lower or "symbol_list" in lower or name.endswith("_symbols"):
            kmi_symbol_lists.append(rel)
        if "protected_modules" in lower:
            protected_modules.append(rel)
        if any(hint in lower for hint in GKI_HINTS):
            gki_files.append(rel)
        if "module_outs" in lower or "module_out" in lower:
            module_outs_files.append(rel)
        if "vendor" in lower and any(token in lower for token in ["module", "drivers", "dlkm"]):
            parts = rel.split("/")
            if parts:
                vendor_module_dirs.add("/".join(parts[: min(4, len(parts))]))

    findings = []
    if not gki_files:
        findings.append({
            "severity": "medium",
            "category": "GKI",
            "message": "No obvious GKI-related files were detected.",
            "suggestion": "Legacy device kernels may be fine, but GKI devices should include GKI build/config/ABI hints.",
        })
    if gki_files and not kmi_symbol_lists:
        findings.append({
            "severity": "medium",
            "category": "KMI",
            "message": "GKI hints were detected, but no KMI symbol list was found.",
            "suggestion": "Review ABI/KMI symbol list handling before changing exported symbols or vendor modules.",
        })
    if gki_files and not protected_modules:
        findings.append({
            "severity": "low",
            "category": "KMI",
            "message": "No protected modules list was detected.",
            "suggestion": "Some Android kernel workflows track protected vendor modules separately. Confirm project requirements.",
        })
    if not module_outs_files and vendor_module_dirs:
        findings.append({
            "severity": "low",
            "category": "Modules",
            "message": "Vendor module folders were detected but no module_outs hints were found.",
            "suggestion": "Confirm expected module packaging for vendor_boot, vendor_dlkm, or recovery workflows.",
        })

    return {
        "root": str(root_path),
        "gki_detected": bool(gki_files),
        "kmi_symbol_lists_detected": bool(kmi_symbol_lists),
        "protected_modules_detected": bool(protected_modules),
        "module_outs_detected": bool(module_outs_files),
        "gki_files": sorted(gki_files)[:120],
        "abi_files": sorted(abi_files)[:120],
        "kmi_symbol_lists": sorted(kmi_symbol_lists)[:80],
        "protected_modules": sorted(protected_modules)[:80],
        "module_outs_files": sorted(module_outs_files)[:80],
        "vendor_module_dirs": sorted(vendor_module_dirs)[:80],
        "findings": findings,
    }
