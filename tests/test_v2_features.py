from __future__ import annotations

from pathlib import Path

from kernelscope.analyzers.build_system import detect_build_system
from kernelscope.analyzers.defconfig_diff import diff_defconfigs
from kernelscope.analyzers.dts_map import build_dts_map
from kernelscope.analyzers.gki import check_gki
from kernelscope.analyzers.module_map import build_module_map
from kernelscope.analyzers.package_checker import check_package
from kernelscope.analyzers.security_audit import run_security_audit
from kernelscope.generators.intelligence_report import write_intelligence_report


def make_kernel(root: Path) -> Path:
    kernel = root / "kernel"
    (kernel / "arch/arm64/configs").mkdir(parents=True)
    (kernel / "arch/arm64/boot/dts/qcom").mkdir(parents=True)
    (kernel / "drivers/camera").mkdir(parents=True)
    (kernel / "android/abi_gki_aarch64").mkdir(parents=True)
    (kernel / "Makefile").write_text("VERSION = 5\nPATCHLEVEL = 10\nSUBLEVEL = 198\nEXTRAVERSION = -android\n", encoding="utf-8")
    (kernel / "arch/arm64/configs/sweet_defconfig").write_text(
        "CONFIG_SECURITY=y\nCONFIG_SECURITY_SELINUX=y\nCONFIG_ANDROID_BINDER_IPC=y\nCONFIG_DEBUG_FS=y\nCONFIG_MODULES=y\n",
        encoding="utf-8",
    )
    (kernel / "arch/arm64/boot/dts/qcom/sweet.dts").write_text(
        "/dts-v1/;\n/ { model = \"sweet\"; panel { }; touchscreen { }; camera { }; thermal-zones { }; };\n",
        encoding="utf-8",
    )
    (kernel / "drivers/camera/Makefile").write_text("obj-$(CONFIG_CAMERA_TEST) += camera_test.o\n", encoding="utf-8")
    (kernel / "build.config.gki.aarch64").write_text("FILES=\"Image modules\"\n", encoding="utf-8")
    (kernel / "MODULE.bazel").write_text("module(name = \"kernel\")\n", encoding="utf-8")
    (kernel / "android/abi_gki_aarch64/symbols").write_text("module_symbol\n", encoding="utf-8")
    (kernel / "anykernel.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (kernel / "Image.gz").write_text("binary", encoding="utf-8")
    return kernel


def test_build_system_and_gki(tmp_path: Path) -> None:
    kernel = make_kernel(tmp_path)
    build = detect_build_system(kernel)
    gki = check_gki(kernel)
    assert build["primary"] == "Kleaf / Bazel"
    assert gki["gki_detected"] is True
    assert gki["kmi_symbol_lists_detected"] is True


def test_dts_module_security_and_package(tmp_path: Path) -> None:
    kernel = make_kernel(tmp_path)
    dts = build_dts_map(kernel)
    modules = build_module_map(kernel)
    security = run_security_audit(kernel)
    package = check_package(kernel)
    assert dts["hardware"]["display"]["detected"] is True
    assert modules["kbuild_entry_count"] == 1
    assert security["inspected_count"] == 1
    assert package["ready"] is True


def test_defconfig_diff(tmp_path: Path) -> None:
    old = tmp_path / "old_defconfig"
    new = tmp_path / "new_defconfig"
    old.write_text("CONFIG_SECURITY_SELINUX=y\nCONFIG_DEBUG_FS=n\n", encoding="utf-8")
    new.write_text("CONFIG_SECURITY_SELINUX=n\nCONFIG_DEBUG_FS=y\n", encoding="utf-8")
    diff = diff_defconfigs(old, new)
    assert diff["changed_count"] == 2
    assert diff["findings"]


def test_intelligence_report(tmp_path: Path) -> None:
    kernel = make_kernel(tmp_path)
    out = tmp_path / "report"
    report = write_intelligence_report(kernel, out)
    assert (out / "summary.md").exists()
    assert (out / "report.html").exists()
    assert report["score"] > 0
