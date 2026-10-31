from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.doctor import run_doctor
from kernelscope.generators.templates import render_template


def generate_report(root: str | Path, output_dir: str | Path, html: bool = True) -> dict[str, Any]:
    data = run_doctor(root)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    markdown = render_template("report.md.j2", data=data)
    md_path = out_dir / "kernel-report.md"
    md_path.write_text(markdown, encoding="utf-8")

    html_path = None
    if html:
        html_text = render_template("report.html.j2", data=data)
        html_path = out_dir / "kernel-report.html"
        html_path.write_text(html_text, encoding="utf-8")

    return {
        "output_dir": str(out_dir),
        "markdown": str(md_path),
        "html": str(html_path) if html_path else "",
        "score": data["score"],
        "finding_count": len(data["findings"]),
    }
