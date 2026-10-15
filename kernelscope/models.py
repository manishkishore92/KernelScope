from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Finding:
    severity: str
    category: str
    message: str
    suggestion: str = ""
    file: Optional[str] = None
    line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KernelSummary:
    path: str
    name: str = "Unknown kernel tree"
    version: str = "Unknown"
    arches: List[str] = field(default_factory=list)
    defconfig_count: int = 0
    dts_count: int = 0
    dtsi_count: int = 0
    module_count: int = 0
    anykernel_detected: bool = False
    findings: List[Finding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["findings"] = [item.to_dict() for item in self.findings]
        return data
