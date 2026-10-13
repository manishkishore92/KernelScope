from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from kernelscope import __version__
from kernelscope.analyzers.anykernel import inspect_anykernel
from kernelscope.analyzers.build_system import detect_build_system
from kernelscope.analyzers.compare import compare_trees
from kernelscope.analyzers.defconfig import inspect_defconfig, inspect_tree_defconfigs
from kernelscope.analyzers.defconfig_diff import diff_defconfigs
from kernelscope.analyzers.doctor import run_doctor
from kernelscope.analyzers.dts import scan_dts
from kernelscope.analyzers.dts_map import build_dts_map
from kernelscope.analyzers.gki import check_gki
from kernelscope.analyzers.intelligence import run_intelligence
from kernelscope.analyzers.logs import analyze_log
from kernelscope.analyzers.module_map import build_module_map
from kernelscope.analyzers.modules import scan_modules
from kernelscope.analyzers.package_checker import check_package
from kernelscope.analyzers.scanner import scan_tree
from kernelscope.analyzers.security_audit import run_security_audit
from kernelscope.analyzers.symbols import scan_symbols
from kernelscope.analyzers.recommendations import build_recommendation_plan
from kernelscope.analyzers.release import release_check
from kernelscope.analyzers.toolchain import check_toolchain
from kernelscope.config import DEFAULT_CONFIG, KernelScopeConfig
from kernelscope.generators.build_plan import generate_build_plan
from kernelscope.generators.enhanced_build import generate_enhanced_build_plan
from kernelscope.generators.intelligence_report import write_intelligence_report
from kernelscope.generators.patch_plan import build_patch_plan, write_patch_plan
from kernelscope.generators.release_notes import write_release_check
from kernelscope.generators.ecosystem_exports import export_android_es, export_rom_harbor, export_droidfoundry
from kernelscope.generators.ci import generate_ci_workflow
from kernelscope.generators.reports import generate_report
from kernelscope.utils.filesystem import write_text
from kernelscope.utils.formats import to_json
from kernelscope.wizard import run_wizard

app = typer.Typer(
    name="kernelscope",
    help="Android kernel inspection and build assistant for ROM maintainers.",
    no_args_is_help=True,
)
console = Console()


def _emit(data: dict | list, json_output: bool, output: Optional[Path] = None) -> None:
    text = to_json(data)
    if output:
        write_text(output, text + "\n")
        console.print(f"[green]Wrote JSON:[/green] {output}")
        return
    if json_output:
        console.print_json(text)
        return


def _print_findings(findings: list[dict]) -> None:
    if not findings:
        console.print("[green]No major findings detected.[/green]")
        return
    table = Table(title="Findings")
    table.add_column("Severity", style="bold")
    table.add_column("Category")
    table.add_column("Message")
    table.add_column("Suggestion")
    for item in findings:
        severity = str(item.get("severity", "low"))
        style = "red" if severity == "high" else "yellow" if severity == "medium" else "green"
        table.add_row(
            f"[{style}]{severity.upper()}[/{style}]",
            str(item.get("category", "")),
            str(item.get("message", item.get("matched", ""))),
            str(item.get("suggestion", "")),
        )
    console.print(table)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", help="Show KernelScope version and exit."),
) -> None:
    if version:
        console.print(f"KernelScope {__version__}")
        raise typer.Exit()


@app.command()
def scan(
    kernel: Path = typer.Argument(..., help="Path to an Android/Linux kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Scan a kernel tree and summarize its structure."""
    data = scan_tree(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit(f"[bold]KernelScope Scan[/bold]\n{data['path']}"))
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Item")
    table.add_column("Value")
    table.add_row("Kernel version", data["kernel_version"])
    table.add_row("Architectures", ", ".join(data["arches"]) or "Not detected")
    table.add_row("Defconfigs", str(data["defconfig_count"]))
    table.add_row("DTS files", str(data["dts_count"]))
    table.add_row("DTSI files", str(data["dtsi_count"]))
    table.add_row("Built modules", str(data["module_count"]))
    table.add_row("AnyKernel3", "Detected" if data["anykernel_detected"] else "Not detected")
    console.print(table)
    _print_findings(data.get("findings", []))


@app.command()
def doctor(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Run a maintainer health check on a kernel tree."""
    data = run_doctor(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit(f"[bold]KernelScope Doctor[/bold]\nReadiness score: [bold]{data['score']}/100[/bold]"))
    _print_findings(data["findings"])


@app.command("defconfig")
def defconfig_command(
    path: Path = typer.Argument(..., help="Path to a defconfig file or kernel tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Inspect defconfig options and Android/security-related settings."""
    data = inspect_defconfig(path) if path.is_file() else inspect_tree_defconfigs(path)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    if "defconfigs" in data:
        console.print(Panel.fit(f"[bold]Defconfig Inspector[/bold]\nInspected {data['inspected_count']} of {data['total_defconfigs']} defconfigs"))
        for item in data["defconfigs"][:8]:
            console.print(f"[cyan]{item['name']}[/cyan]: {item['option_count']} options, {item['enabled']} enabled, {item['modules']} modules")
    else:
        console.print(Panel.fit(f"[bold]{data['name']}[/bold]\n{data['option_count']} options"))
        console.print(f"Enabled: {data['enabled']}  Modules: {data['modules']}  Not set: {data['not_set']}")
        _print_findings(data.get("findings", []))


@app.command("diff-defconfig")
def diff_defconfig_command(
    old: Path = typer.Argument(..., help="Old defconfig file."),
    new: Path = typer.Argument(..., help="New defconfig file."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Compare two defconfig files and highlight Android/security changes."""
    data = diff_defconfigs(old, new)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit("[bold]Defconfig Diff[/bold]"))
    console.print(f"Added: {data['added_count']}  Removed: {data['removed_count']}  Changed: {data['changed_count']}")
    if data["important_changes"]:
        table = Table(title="Important Changes")
        table.add_column("Config")
        table.add_column("Old")
        table.add_column("New")
        table.add_column("Category")
        for item in data["important_changes"][:40]:
            table.add_row(item["config"], item["old"], item["new"], item["category"])
        console.print(table)
    _print_findings(data.get("findings", []))


@app.command()
def dts(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Scan DTS/DTSI files and device-tree hints."""
    data = scan_dts(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    table = Table(title="DTS Scan")
    table.add_column("Item")
    table.add_column("Value")
    table.add_row("DTS", str(data["dts_files"]))
    table.add_row("DTSI", str(data["dtsi_files"]))
    table.add_row("Vendor hints", str(data["vendor_hints"]))
    table.add_row("Overlay candidates", str(len(data["overlay_candidates"])))
    console.print(table)


@app.command("dts-map")
def dts_map_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Create a hardware-oriented map from DTS/DTSI files."""
    data = build_dts_map(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    table = Table(title="DTS Hardware Map")
    table.add_column("Category")
    table.add_column("Status")
    table.add_column("Matches")
    for name, item in data["hardware"].items():
        table.add_row(name.replace("_", " ").title(), "Detected" if item["detected"] else "Not detected", str(item["count"]))
    console.print(table)
    _print_findings(data.get("findings", []))


@app.command()
def modules(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Inspect module outputs and Kbuild module rules."""
    data = scan_modules(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    table = Table(title="Module Scan")
    table.add_column("Item")
    table.add_column("Value")
    table.add_row("Built .ko modules", str(data["built_module_count"]))
    table.add_row("modules.order files", str(len(data["module_order_files"])))
    table.add_row("Module.symvers files", str(len(data["module_symvers_files"])))
    table.add_row("Kbuild entries", str(data["kbuild_entry_count"]))
    console.print(table)


@app.command("module-map")
def module_map_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Create a categorized map of kernel modules and Kbuild rules."""
    data = build_module_map(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    table = Table(title="Kernel Module Map")
    table.add_column("Category")
    table.add_column("Items")
    for category, items in data["categories"].items():
        table.add_row(category.replace("_", " ").title(), str(len(items)))
    console.print(table)
    _print_findings(data.get("findings", []))


@app.command("toolchain")
def toolchain_command(
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Check common Android kernel build tools in PATH."""
    data = check_toolchain()
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    table = Table(title="Toolchain Check")
    table.add_column("Tool")
    table.add_column("Status")
    table.add_column("Path")
    for item in data["tools"]:
        table.add_row(item["tool"], "[green]found[/green]" if item["found"] else "[red]missing[/red]", item["path"])
    console.print(table)


@app.command("anykernel")
def anykernel_command(
    path: Path = typer.Argument(..., help="Path to an AnyKernel3 folder or kernel tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Check AnyKernel3 packaging files."""
    data = inspect_anykernel(path)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit(f"[bold]AnyKernel3[/bold]\n{data['notes']}"))
    console.print(f"Markers: {', '.join(data['markers']) or 'None'}")


@app.command("package-check")
def package_check_command(
    path: Path = typer.Argument(..., help="Path to AnyKernel3 package folder or kernel output folder."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Check kernel release package readiness."""
    data = check_package(path)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit(f"[bold]Package Check[/bold]\nReady: {'yes' if data['ready'] else 'needs review'}"))
    console.print(f"Images: {len(data['image_files'])}  Modules: {data['module_count']}")
    _print_findings(data.get("findings", []))


@app.command("analyze-log")
def analyze_log_command(
    log: Path = typer.Argument(..., help="Path to a kernel build log."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Analyze kernel build logs and suggest likely fixes."""
    data = analyze_log(log)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit(f"[bold]Build Log Analyzer[/bold]\nFindings: {data['finding_count']}"))
    _print_findings(data["findings"])


@app.command("build-system")
def build_system_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Detect kernel build system style."""
    data = detect_build_system(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit(f"[bold]Build System[/bold]\nPrimary: {data['primary']}"))
    console.print("Detected: " + (", ".join(data["systems"]) or "None"))
    _print_findings(data.get("findings", []))


@app.command("gki-check")
def gki_check_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Check GKI/KMI readiness hints."""
    data = check_gki(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    table = Table(title="GKI / KMI Check")
    table.add_column("Item")
    table.add_column("Status")
    table.add_row("GKI hints", "Detected" if data["gki_detected"] else "Not detected")
    table.add_row("KMI symbol lists", "Detected" if data["kmi_symbol_lists_detected"] else "Not detected")
    table.add_row("Protected modules", "Detected" if data["protected_modules_detected"] else "Not detected")
    table.add_row("module_outs", "Detected" if data["module_outs_detected"] else "Not detected")
    console.print(table)
    _print_findings(data.get("findings", []))


@app.command("security")
def security_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Run deeper Android/security config checks across defconfigs."""
    data = run_security_audit(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit(f"[bold]Security Config Audit[/bold]\nInspected {data['inspected_count']} of {data['defconfig_count']} defconfigs"))
    _print_findings(data.get("findings", []))


@app.command("build-plan")
def build_plan_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to kernelscope.yml."),
    output: Path = typer.Option(Path("build-kernel.sh"), "--output", "-o", help="Generated build script path."),
) -> None:
    """Generate a reviewable kernel build script."""
    cfg = KernelScopeConfig.from_file(config)
    result = generate_build_plan(kernel, cfg, output=output)
    console.print(f"[green]Generated build plan:[/green] {result['output']}")


@app.command("build-plan-full")
def build_plan_full_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to kernelscope.yml."),
    output: Path = typer.Option(Path("kernel-build-plan"), "--output", "-o", help="Generated build plan folder."),
) -> None:
    """Generate Make/Kleaf helper scripts and environment notes."""
    cfg = KernelScopeConfig.from_file(config)
    result = generate_enhanced_build_plan(kernel, cfg, output)
    console.print(f"[green]Generated build plan folder:[/green] {result['output_dir']}")
    for name, path in result["files"].items():
        console.print(f"- {name}: {path}")


@app.command()
def report(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    output: Path = typer.Option(Path("kernelscope-report"), "--output", "-o", help="Report output folder."),
    html: bool = typer.Option(True, "--html/--no-html", help="Generate HTML report too."),
) -> None:
    """Generate Markdown and HTML maintainer reports."""
    result = generate_report(kernel, output, html=html)
    console.print(f"[green]Generated report folder:[/green] {result['output_dir']}")
    console.print(f"Markdown: {result['markdown']}")
    if result["html"]:
        console.print(f"HTML: {result['html']}")


@app.command("intelligence")
def intelligence_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    output: Path = typer.Option(Path("kernel-intelligence-report"), "--output", "-o", help="Output report folder."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of writing files."),
) -> None:
    """Run all major analyzers and generate a maintainer intelligence report."""
    if json_output:
        data = run_intelligence(kernel)
        _emit(data, json_output=True)
        return
    result = write_intelligence_report(kernel, output, html=True)
    console.print(f"[green]Generated intelligence report:[/green] {result['output_dir']}")
    console.print(f"Score: {result['score']}/100  Findings: {result['finding_count']}")


@app.command("html-report")
def html_report_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    output: Path = typer.Option(Path("kernel-report-html"), "--output", "-o", help="Output folder."),
) -> None:
    """Generate an offline HTML report."""
    result = write_intelligence_report(kernel, output, html=True)
    console.print(f"[green]Generated HTML report:[/green] {result['paths'].get('report.html')}")


@app.command("symbols")
def symbols_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Inspect exported symbols, Module.symvers, and KMI/ABI symbol lists."""
    data = scan_symbols(kernel)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    table = Table(title="Symbol Intelligence")
    table.add_column("Item")
    table.add_column("Value")
    table.add_row("Source files scanned", str(data["source_files_scanned"]))
    table.add_row("Module.symvers files", str(data["symvers_file_count"]))
    table.add_row("Symvers symbols", str(data["symvers_symbol_count"]))
    table.add_row("Unique exported symbols", str(data["unique_exported_symbol_count"]))
    table.add_row("KMI/ABI files", str(data["kmi_file_count"]))
    console.print(table)
    _print_findings(data.get("findings", []))


@app.command("recommend")
def recommend_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Create a prioritized maintainer recommendation plan."""
    plan = build_recommendation_plan(run_intelligence(kernel))
    if json_output or output:
        _emit(plan, json_output=True, output=output)
        return
    console.print(Panel.fit(f"[bold]Recommendation Plan[/bold]\nFindings: {plan['summary']['finding_count']}"))
    for title, key in [("Immediate", "immediate"), ("Before Build", "before_build"), ("Before Release", "before_release")]:
        console.print(f"[bold cyan]{title}[/bold cyan]")
        for item in plan[key]:
            console.print(f"- {item}")


@app.command("patch-plan")
def patch_plan_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    output: Path = typer.Option(Path("kernel-patch-plan"), "--output", "-o", help="Output folder for patch plan files."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
) -> None:
    """Generate a safe patch/review plan without modifying the kernel tree."""
    if json_output:
        _emit(build_patch_plan(kernel), json_output=True)
        return
    result = write_patch_plan(kernel, output)
    console.print(f"[green]Generated patch plan:[/green] {result['output_dir']}")
    console.print(f"Review items: {result['patch_count']}")


@app.command("release-check")
def release_check_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    package: Optional[Path] = typer.Option(None, "--package", "-p", help="AnyKernel3/package/output folder. Defaults to kernel path."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write release report folder."),
    checksum: bool = typer.Option(False, "--checksum", help="Calculate SHA-256 for detected release artifacts."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
) -> None:
    """Review kernel release/package artifacts and optional checksums."""
    if output:
        result = write_release_check(kernel, output, package=package, checksum=checksum)
        console.print(f"[green]Generated release check:[/green] {result['output_dir']}")
        console.print(f"Artifacts: {result['artifact_count']}")
        return
    data = release_check(kernel, package=package, checksum=checksum)
    if json_output:
        _emit(data, json_output=True)
        return
    console.print(Panel.fit(f"[bold]Release Check[/bold]\nArtifacts: {data['artifact_count']}\nReady: {'yes' if data['package_ready'] else 'needs review'}"))
    for item in data["artifacts"][:20]:
        checksum_text = f"  {item.get('sha256', '')}" if item.get("sha256") else ""
        console.print(f"- {item['path']} ({item['human_size']}){checksum_text}")
    _print_findings(data.get("findings", []))


@app.command("export-android-es")
def export_android_es_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    output: Path = typer.Option(Path("android-es-export"), "--output", "-o", help="Output folder."),
    device: str = typer.Option("", "--device", help="Device codename."),
    brand: str = typer.Option("", "--brand", help="Device brand."),
    maintainer: str = typer.Option("", "--maintainer", help="Maintainer name or handle."),
) -> None:
    """Export a KernelScope profile for android-es."""
    result = export_android_es(kernel, output, device=device, brand=brand, maintainer=maintainer)
    console.print(f"[green]Generated android-es export:[/green] {result['output_dir']}")


@app.command("export-rom-harbor")
def export_rom_harbor_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    output: Path = typer.Option(Path("rom-harbor-export"), "--output", "-o", help="Output folder."),
    device: str = typer.Option("", "--device", help="Device codename."),
    maintainer: str = typer.Option("", "--maintainer", help="Maintainer name or handle."),
) -> None:
    """Export kernel release metadata for ROM Harbor."""
    result = export_rom_harbor(kernel, output, device=device, maintainer=maintainer)
    console.print(f"[green]Generated ROM Harbor export:[/green] {result['output_dir']}")


@app.command("export-droidfoundry")
def export_droidfoundry_command(
    kernel: Path = typer.Argument(..., help="Path to a kernel source tree."),
    output: Path = typer.Option(Path("droidfoundry-export"), "--output", "-o", help="Output folder."),
    device: str = typer.Option("", "--device", help="Device codename."),
    maintainer: str = typer.Option("", "--maintainer", help="Maintainer name or handle."),
) -> None:
    """Export kernel handoff data for DroidFoundry workflows."""
    result = export_droidfoundry(kernel, output, device=device, maintainer=maintainer)
    console.print(f"[green]Generated DroidFoundry export:[/green] {result['output_dir']}")


@app.command("ci-export")
def ci_export_command(
    output: Path = typer.Option(Path("kernelscope-report.yml"), "--output", "-o", help="Workflow YAML path or output folder."),
    python_version: str = typer.Option("3.12", "--python", help="Python version for the workflow."),
) -> None:
    """Generate an optional GitHub Actions workflow file for report automation."""
    result = generate_ci_workflow(output, python_version=python_version)
    console.print(f"[green]Generated workflow:[/green] {result['path']}")


@app.command()
def compare(
    old: Path = typer.Argument(..., help="Old kernel tree path."),
    new: Path = typer.Argument(..., help="New kernel tree path."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to a file."),
) -> None:
    """Compare two kernel trees at a high level."""
    data = compare_trees(old, new)
    if json_output or output:
        _emit(data, json_output=True, output=output)
        return
    console.print(Panel.fit("[bold]Kernel Tree Compare[/bold]"))
    console.print(f"Kernel version: {data['kernel_version']['old']} -> {data['kernel_version']['new']}")
    console.print(f"Defconfigs added: {len(data['defconfigs_added'])}")
    console.print(f"Defconfigs removed: {len(data['defconfigs_removed'])}")


@app.command("wizard")
def wizard_command() -> None:
    """Open an interactive report/build-plan wizard."""
    run_wizard()


@app.command("init-config")
def init_config(
    output: Path = typer.Option(Path("kernelscope.yml"), "--output", "-o", help="Config file path."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config."),
) -> None:
    """Create a starter kernelscope.yml file."""
    if output.exists() and not force:
        console.print(f"[yellow]Config already exists:[/yellow] {output}")
        raise typer.Exit(code=1)
    write_text(output, DEFAULT_CONFIG)
    console.print(f"[green]Created config:[/green] {output}")
