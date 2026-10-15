from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kernelscope.utils.formats import load_yaml


@dataclass
class KernelScopeConfig:
    device: str = "generic"
    arch: str = "arm64"
    subarch: str = "arm64"
    defconfig: str = ""
    clang_path: str = ""
    gcc_prefix: str = ""
    anykernel_path: str = ""
    output_dir: str = "kernelscope-output"
    jobs: int = 8

    @classmethod
    def from_file(cls, path: str | Path | None) -> "KernelScopeConfig":
        if not path:
            return cls()
        raw = load_yaml(path)
        build = raw.get("build", {}) if isinstance(raw, dict) else {}
        return cls(
            device=str(raw.get("device", "generic")),
            arch=str(build.get("arch", raw.get("arch", "arm64"))),
            subarch=str(build.get("subarch", raw.get("subarch", "arm64"))),
            defconfig=str(build.get("defconfig", raw.get("defconfig", ""))),
            clang_path=str(build.get("clang_path", raw.get("clang_path", ""))),
            gcc_prefix=str(build.get("gcc_prefix", raw.get("gcc_prefix", ""))),
            anykernel_path=str(raw.get("anykernel_path", "")),
            output_dir=str(raw.get("output_dir", "kernelscope-output")),
            jobs=int(build.get("jobs", raw.get("jobs", 8)) or 8),
        )


DEFAULT_CONFIG = """# KernelScope configuration
# Edit these values for your Android kernel tree.

device: sweet
output_dir: kernelscope-output
anykernel_path: ./AnyKernel3

build:
  arch: arm64
  subarch: arm64
  defconfig: vendor/sweet_defconfig
  clang_path: ~/toolchains/clang/bin
  gcc_prefix: aarch64-linux-android-
  jobs: 8
"""
