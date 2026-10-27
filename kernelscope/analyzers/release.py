from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from kernelscope.analyzers.package_checker import check_package
from kernelscope.analyzers.scanner import scan_tree
from kernelscope.utils.filesystem import file_size, relative, require_path, walk_files
from kernelscope.utils.formats import human_size

RELEASE_SUFFIXES = {".zip", ".img", ".gz", ".dtb", ".ko"}
IMAGE_NAMES = {"Image", "Image.gz", "Image.gz-dtb", "dtbo.img", "vendor_boot.img", "boot.img"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def release_check(kernel: str | Path, package: str | Path | None = None, checksum: bool = False) -> dict[str, Any]:
    kernel_path = require_path(kernel, "kernel tree")
    package_path = Path(package).expanduser().resolve() if package else kernel_path
    if not package_path.exists():
        raise FileNotFoundError(f"package path does not exist: {package_path}")

    scan = scan_tree(kernel_path)
    package_info = check_package(package_path)
    artifacts: list[dict[str, Any]] = []
    for file in walk_files(package_path):
        if file.name in IMAGE_NAMES or file.suffix.lower() in RELEASE_SUFFIXES:
            size = file_size(file)
            item: dict[str, Any] = {
                "path": relative(file, package_path),
                "size": size,
                "human_size": human_size(size),
            }
            if checksum and size <= 2_500_000_000:
                item["sha256"] = sha256_file(file)
            artifacts.append(item)
    artifacts = sorted(artifacts, key=lambda item: item["path"])[:300]

    findings = list(package_info.get("findings", []))
    if not artifacts:
        findings.append({
            "severity": "high",
            "category": "Release package",
            "message": "No release artifacts were detected in the selected package/output path.",
            "suggestion": "Point --package to AnyKernel3, the kernel output folder, or a prepared release directory.",
        })
    if not any(item["path"].endswith(".zip") for item in artifacts):
        findings.append({
            "severity": "low",
            "category": "Release package",
            "message": "No flashable ZIP was detected.",
            "suggestion": "This is fine for image-only workflows, but standalone kernel releases usually include an AnyKernel3 ZIP.",
        })

    return {
        "kernel": str(kernel_path),
        "package": str(package_path),
        "kernel_version": scan.get("kernel_version"),
        "package_ready": package_info.get("ready"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "package_info": package_info,
        "findings": findings,
    }
