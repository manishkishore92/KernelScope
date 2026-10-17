from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import find_by_name, relative, require_path, walk_files


def inspect_anykernel(path: str | Path) -> dict[str, Any]:
    root = require_path(path, "AnyKernel3 or kernel tree")
    markers = find_by_name(root, ["anykernel.sh", "ak3-core.sh", "update-binary"])
    ramdisk_files = []
    tools = []
    image_candidates = []
    for file in walk_files(root):
        rel = relative(file, root)
        parts = set(file.parts)
        if "ramdisk" in parts:
            ramdisk_files.append(rel)
        if "tools" in parts:
            tools.append(rel)
        if file.name in {"Image", "Image.gz", "Image.gz-dtb", "dtbo.img", "vendor_boot.img"}:
            image_candidates.append(rel)
    return {
        "path": str(root),
        "detected": bool(markers),
        "markers": [relative(marker, root) for marker in markers],
        "ramdisk_file_count": len(ramdisk_files),
        "tool_file_count": len(tools),
        "image_candidates": image_candidates[:50],
        "notes": "Detected AnyKernel3-style packaging files." if markers else "No AnyKernel3 marker files were detected.",
    }
