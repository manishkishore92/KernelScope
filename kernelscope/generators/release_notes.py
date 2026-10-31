from __future__ import annotations

from pathlib import Path
from typing import Any

from kernelscope.analyzers.release import release_check
from kernelscope.generators.templates import render_template
from kernelscope.utils.filesystem import write_text
from kernelscope.utils.formats import to_json


def write_release_check(kernel: str | Path, output: str | Path, package: str | Path | None = None, checksum: bool = False) -> dict[str, Any]:
    data = release_check(kernel, package=package, checksum=checksum)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "release-check.md": str(write_text(out / "release-check.md", render_template("release-check.md.j2", data=data))),
        "release-check.json": str(write_text(out / "release-check.json", to_json(data) + "\n")),
    }
    if data.get("artifacts"):
        checksum_lines = []
        for item in data["artifacts"]:
            if item.get("sha256"):
                checksum_lines.append(f"{item['sha256']}  {item['path']}")
        if checksum_lines:
            paths["SHA256SUMS"] = str(write_text(out / "SHA256SUMS", "\n".join(checksum_lines) + "\n"))
    return {"output_dir": str(out), "artifact_count": data["artifact_count"], "paths": paths}
