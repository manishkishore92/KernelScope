from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kernelscope.analyzers.intelligence import run_intelligence
from kernelscope.analyzers.recommendations import build_recommendation_plan
from kernelscope.generators.build_plan import generate_build_plan
from kernelscope.generators.templates import render_template
from kernelscope.config import KernelScopeConfig
from kernelscope.utils.filesystem import write_text
from kernelscope.utils.formats import to_json


def write_intelligence_report(root: str | Path, output_dir: str | Path, html: bool = True) -> dict[str, Any]:
    data = run_intelligence(root)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths: dict[str, str] = {}
    recommendations = build_recommendation_plan(data)
    files = {
        "summary.md": render_template("intelligence-summary.md.j2", data=data),
        "security-report.md": render_template("security-report.md.j2", data=data),
        "dts-map.md": render_template("dts-map.md.j2", data=data),
        "module-map.md": render_template("module-map.md.j2", data=data),
        "symbol-report.md": render_template("symbol-report.md.j2", data=data["symbols"]),
        "build-system.md": render_template("build-system.md.j2", data=data),
        "recommendations.md": render_template("recommendations.md.j2", plan=recommendations),
        "issues.json": to_json(data.get("findings", [])) + "\n",
        "intelligence.json": to_json(data) + "\n",
    }
    for filename, content in files.items():
        paths[filename] = str(write_text(out / filename, content))

    cfg = KernelScopeConfig()
    plan = generate_build_plan(root, cfg, output=out / "build-plan.sh")
    paths["build-plan.sh"] = plan["output"]

    if html:
        paths["report.html"] = str(write_text(out / "report.html", render_template("intelligence-report.html.j2", data=data)))

    return {
        "output_dir": str(out),
        "score": data["readiness"]["score"],
        "finding_count": len(data.get("findings", [])),
        "paths": paths,
    }
