from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from kernelscope.utils.filesystem import relative, require_path, walk_files

OBJ_RE = re.compile(r"^\s*obj-\$?\(?([A-Za-z0-9_]+)?\)?\s*\+=\s*(.+)$")


def scan_modules(root: str | Path) -> dict[str, Any]:
    root_path = require_path(root, "kernel tree")
    ko_files = []
    module_orders = []
    symvers = []
    kbuild_entries = []

    for path in walk_files(root_path):
        rel = relative(path, root_path)
        if path.suffix == ".ko":
            ko_files.append(rel)
        elif path.name == "modules.order":
            module_orders.append(rel)
        elif path.name == "Module.symvers":
            symvers.append(rel)
        elif path.name in {"Makefile", "Kbuild"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = OBJ_RE.match(line)
                if match and ".o" in match.group(2):
                    kbuild_entries.append({"file": rel, "line": line_no, "rule": line.strip()})
                    if len(kbuild_entries) >= 200:
                        break

    return {
        "root": str(root_path),
        "built_modules": ko_files[:100],
        "built_module_count": len(ko_files),
        "module_order_files": module_orders,
        "module_symvers_files": symvers,
        "kbuild_entry_count": len(kbuild_entries),
        "kbuild_examples": kbuild_entries[:50],
    }
