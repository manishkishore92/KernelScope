from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.build_system import detect_build_system
from kernelscope.config import KernelScopeConfig
from kernelscope.generators.templates import render_template
from kernelscope.utils.filesystem import write_text


def generate_enhanced_build_plan(root: str | Path, config: KernelScopeConfig, output_dir: str | Path) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    build_system = detect_build_system(root)
    created: dict[str, str] = {}

    created["build-kernel.sh"] = str(write_text(out / "build-kernel.sh", render_template("build_plan.sh.j2", root=str(Path(root).resolve()), config=config)))
    Path(created["build-kernel.sh"]).chmod(0o755)

    if "Kleaf / Bazel" in build_system.get("systems", []):
        created["build-kleaf.sh"] = str(write_text(out / "build-kleaf.sh", render_template("build-kleaf.sh.j2", root=str(Path(root).resolve()), config=config, build_system=build_system)))
        Path(created["build-kleaf.sh"]).chmod(0o755)

    if "Makefile" in build_system.get("systems", []):
        created["build-make.sh"] = str(write_text(out / "build-make.sh", render_template("build-make.sh.j2", root=str(Path(root).resolve()), config=config, build_system=build_system)))
        Path(created["build-make.sh"]).chmod(0o755)

    created["environment-notes.md"] = str(write_text(out / "environment-notes.md", render_template("environment-notes.md.j2", root=str(Path(root).resolve()), config=config, build_system=build_system)))
    return {"output_dir": str(out), "build_system": build_system.get("primary"), "files": created}
