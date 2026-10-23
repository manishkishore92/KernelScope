from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import find_by_name, relative, require_path, walk_files

EXPECTED = {
    "anykernel.sh": "AnyKernel3 installer script",
    "META-INF": "Flashable ZIP metadata folder",
}
IMAGE_NAMES = {"Image", "Image.gz", "Image.gz-dtb", "dtbo.img", "vendor_boot.img", "boot.img"}


def check_package(path: str | Path) -> dict[str, Any]:
    root = require_path(path, "AnyKernel3 package or kernel output")
    files = list(walk_files(root))
    image_files = [relative(item, root) for item in files if item.name in IMAGE_NAMES]
    marker_files = [relative(item, root) for item in find_by_name(root, ["anykernel.sh", "ak3-core.sh", "update-binary"])]
    modules = [relative(item, root) for item in files if item.suffix == ".ko"]
    meta_inf = (root / "META-INF").exists()
    tools = [relative(item, root) for item in files if "tools" in item.parts]
    ramdisk = [relative(item, root) for item in files if "ramdisk" in item.parts]

    findings = []
    if not marker_files:
        findings.append({
            "severity": "high",
            "category": "Package",
            "message": "AnyKernel3 marker script was not detected.",
            "suggestion": "Make sure anykernel.sh exists at the package root before creating a flashable ZIP.",
        })
    if not image_files:
        findings.append({
            "severity": "medium",
            "category": "Package",
            "message": "No kernel image or boot image candidate was detected.",
            "suggestion": "Copy Image.gz, Image.gz-dtb, dtbo.img, vendor_boot.img, or boot.img into the expected packaging location.",
        })
    if not meta_inf:
        findings.append({
            "severity": "low",
            "category": "Package",
            "message": "META-INF folder was not detected.",
            "suggestion": "Some AnyKernel3 workflows generate packaging metadata separately; confirm your ZIP build process.",
        })

    return {
        "path": str(root),
        "ready": not any(item["severity"] == "high" for item in findings),
        "marker_files": marker_files,
        "image_files": sorted(image_files),
        "module_files": sorted(modules)[:120],
        "module_count": len(modules),
        "meta_inf": meta_inf,
        "tools_count": len(tools),
        "ramdisk_count": len(ramdisk),
        "findings": findings,
    }
