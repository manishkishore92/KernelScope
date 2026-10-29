from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.config import KernelScopeConfig
from kernelscope.generators.templates import render_template


def generate_build_plan(root: str | Path, config: KernelScopeConfig, output: str | Path | None = None) -> dict[str, Any]:
    script = render_template("build_plan.sh.j2", root=str(Path(root).expanduser().resolve()), config=config)
    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(script, encoding="utf-8")
        out.chmod(0o755)
        return {"output": str(out), "script": script}
    return {"output": "", "script": script}
