from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.defconfig import inspect_tree_defconfigs
from kernelscope.analyzers.intelligence import run_intelligence
from kernelscope.generators.templates import render_template
from kernelscope.utils.filesystem import write_text
from kernelscope.utils.formats import to_json


def build_patch_plan(root: str | Path) -> dict[str, Any]:
    data = run_intelligence(root)
    defconfigs = inspect_tree_defconfigs(root, limit=5).get("defconfigs", [])
    patch_items: list[dict[str, Any]] = []

    for finding in data.get("findings", []):
        category = str(finding.get("category", "General"))
        message = str(finding.get("message", ""))
        suggestion = str(finding.get("suggestion", ""))
        severity = str(finding.get("severity", "low"))
        target = finding.get("file") or "review-needed"
        action = "review"
        if "defconfig" in category.lower() or "config" in message.lower():
            action = "defconfig-review"
        elif "DTS" in category or "device tree" in message.lower():
            action = "dts-review"
        elif "Build" in category:
            action = "build-system-review"
        elif "Packaging" in category or "package" in category.lower():
            action = "package-review"
        patch_items.append({
            "severity": severity,
            "category": category,
            "target": target,
            "action": action,
            "message": message,
            "suggestion": suggestion,
        })

    if not patch_items:
        patch_items.append({
            "severity": "info",
            "category": "Patch plan",
            "target": defconfigs[0]["path"] if defconfigs else "kernel tree",
            "action": "build-validation",
            "message": "No obvious patch targets were detected.",
            "suggestion": "Run a full build and use analyze-log if the build fails.",
        })

    return {
        "root": data.get("root"),
        "score": data.get("readiness", {}).get("score"),
        "patch_count": len(patch_items),
        "patch_items": patch_items[:120],
    }


def write_patch_plan(root: str | Path, output_dir: str | Path) -> dict[str, Any]:
    plan = build_patch_plan(root)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "patch-plan.md": render_template("patch-plan.md.j2", plan=plan),
        "patch-plan.json": to_json(plan) + "\n",
    }
    paths = {name: str(write_text(out / name, content)) for name, content in files.items()}
    return {"output_dir": str(out), "patch_count": plan["patch_count"], "paths": paths}
