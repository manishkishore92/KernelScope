from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.generators.templates import render_template
from kernelscope.utils.filesystem import write_text


def generate_ci_workflow(output: str | Path, python_version: str = "3.12") -> dict[str, Any]:
    out = Path(output)
    if out.suffix in {".yml", ".yaml"}:
        path = out
    else:
        path = out / "kernelscope-report.yml"
    content = render_template("github-workflow.yml.j2", python_version=python_version)
    write_text(path, content)
    return {"path": str(path)}
