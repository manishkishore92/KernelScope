from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.intelligence import run_intelligence
from kernelscope.generators.templates import render_template
from kernelscope.utils.filesystem import write_text
from kernelscope.utils.formats import to_json


def _base_data(root: str | Path, device: str = "", maintainer: str = "") -> dict[str, Any]:
    data = run_intelligence(root)
    data["export"] = {"device": device or "unknown", "maintainer": maintainer or "unknown"}
    return data


def export_android_es(root: str | Path, output: str | Path, device: str = "", brand: str = "", maintainer: str = "") -> dict[str, Any]:
    data = _base_data(root, device=device, maintainer=maintainer)
    data["export"]["brand"] = brand or "unknown"
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "android-es-profile.conf": str(write_text(out / "android-es-profile.conf", render_template("android-es-profile.conf.j2", data=data))),
        "android-es-kernel-report.md": str(write_text(out / "android-es-kernel-report.md", render_template("android-es-kernel-report.md.j2", data=data))),
        "android-es-kernel.json": str(write_text(out / "android-es-kernel.json", to_json(data) + "\n")),
    }
    return {"output_dir": str(out), "paths": paths}


def export_rom_harbor(root: str | Path, output: str | Path, device: str = "", maintainer: str = "") -> dict[str, Any]:
    data = _base_data(root, device=device, maintainer=maintainer)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "device": data["export"]["device"],
        "maintainer": data["export"]["maintainer"],
        "kernelVersion": data.get("scan", {}).get("kernel_version"),
        "readinessScore": data.get("readiness", {}).get("score"),
        "buildSystem": data.get("build_system", {}).get("primary"),
        "gkiDetected": data.get("gki", {}).get("gki_detected"),
        "securityFindingCount": len(data.get("security", {}).get("findings", [])),
        "topFindings": data.get("findings", [])[:20],
        "nextSteps": data.get("next_steps", []),
    }
    paths = {
        "rom-harbor-kernel.json": str(write_text(out / "rom-harbor-kernel.json", to_json(payload) + "\n")),
        "rom-harbor-kernel-notes.md": str(write_text(out / "rom-harbor-kernel-notes.md", render_template("rom-harbor-kernel-notes.md.j2", data=data))),
    }
    return {"output_dir": str(out), "paths": paths}


def export_droidfoundry(root: str | Path, output: str | Path, device: str = "", maintainer: str = "") -> dict[str, Any]:
    data = _base_data(root, device=device, maintainer=maintainer)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    handoff = {
        "tool": "KernelScope",
        "device": data["export"]["device"],
        "maintainer": data["export"]["maintainer"],
        "kernel": {
            "path": data.get("root"),
            "version": data.get("scan", {}).get("kernel_version"),
            "arches": data.get("scan", {}).get("arches", []),
            "defconfigs": data.get("scan", {}).get("defconfigs", [])[:20],
            "dtsCount": data.get("scan", {}).get("dts_count"),
            "moduleCount": data.get("scan", {}).get("module_count"),
        },
        "readiness": data.get("readiness"),
        "findings": data.get("findings", [])[:80],
    }
    paths = {
        "droidfoundry-kernel-handoff.json": str(write_text(out / "droidfoundry-kernel-handoff.json", to_json(handoff) + "\n")),
        "droidfoundry-kernel-handoff.md": str(write_text(out / "droidfoundry-kernel-handoff.md", render_template("droidfoundry-kernel-handoff.md.j2", data=data))),
    }
    return {"output_dir": str(out), "paths": paths}
