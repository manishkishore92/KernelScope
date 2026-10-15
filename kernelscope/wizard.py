from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from kernelscope.analyzers.build_system import detect_build_system
from kernelscope.analyzers.scanner import find_defconfigs, scan_tree
from kernelscope.config import KernelScopeConfig
from kernelscope.generators.enhanced_build import generate_enhanced_build_plan
from kernelscope.generators.intelligence_report import write_intelligence_report

console = Console()


def run_wizard() -> dict[str, Any]:
    console.print("[bold cyan]KernelScope Wizard[/bold cyan]")
    kernel_path = Path(typer.prompt("Kernel source path", default="." )).expanduser().resolve()
    device = typer.prompt("Device codename", default="generic")
    output = Path(typer.prompt("Output folder", default="kernelscope-output"))

    scan = scan_tree(kernel_path)
    build_system = detect_build_system(kernel_path)
    defconfigs = find_defconfigs(kernel_path)
    default_defconfig = defconfigs[0] if defconfigs else ""
    defconfig = typer.prompt("Defconfig", default=default_defconfig or "vendor/device_defconfig")
    arch = "arm64" if "arm64" in scan.get("arches", []) else (scan.get("arches") or ["arm64"])[0]
    jobs = int(typer.prompt("Parallel jobs", default="8"))

    cfg = KernelScopeConfig(device=device, arch=arch, subarch=arch, defconfig=defconfig, output_dir=str(output), jobs=jobs)
    report = write_intelligence_report(kernel_path, output / "report", html=True)
    build_plan = generate_enhanced_build_plan(kernel_path, cfg, output / "build")

    console.print(f"[green]Report:[/green] {report['output_dir']}")
    console.print(f"[green]Build plan:[/green] {build_plan['output_dir']}")
    return {
        "kernel": str(kernel_path),
        "device": device,
        "arch": arch,
        "defconfig": defconfig,
        "build_system": build_system.get("primary"),
        "report": report,
        "build_plan": build_plan,
    }
