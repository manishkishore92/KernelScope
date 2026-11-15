from __future__ import annotations

from pathlib import Path

from kernelscope.analyzers.release import release_check
from kernelscope.analyzers.symbols import scan_symbols
from kernelscope.generators.ci import generate_ci_workflow
from kernelscope.generators.ecosystem_exports import export_android_es, export_droidfoundry, export_rom_harbor
from kernelscope.generators.patch_plan import build_patch_plan, write_patch_plan
from kernelscope.generators.release_notes import write_release_check


def make_kernel(root: Path) -> Path:
    kernel = root / "kernel"
    (kernel / "arch/arm64/configs").mkdir(parents=True)
    (kernel / "arch/arm64/boot/dts/qcom").mkdir(parents=True)
    (kernel / "drivers/test").mkdir(parents=True)
    (kernel / "android/abi_gki_aarch64").mkdir(parents=True)
    (kernel / "Makefile").write_text("VERSION = 5\nPATCHLEVEL = 15\nSUBLEVEL = 123\n", encoding="utf-8")
    (kernel / "arch/arm64/configs/test_defconfig").write_text(
        "CONFIG_SECURITY=y\nCONFIG_SECURITY_SELINUX=y\nCONFIG_ANDROID_BINDER_IPC=y\nCONFIG_MODULES=y\n",
        encoding="utf-8",
    )
    (kernel / "arch/arm64/boot/dts/qcom/test.dts").write_text("/dts-v1/;\n/ { panel { }; camera { }; };\n", encoding="utf-8")
    (kernel / "drivers/test/test.c").write_text("int test_symbol(void){return 0;}\nEXPORT_SYMBOL(test_symbol);\n", encoding="utf-8")
    (kernel / "drivers/test/Makefile").write_text("obj-$(CONFIG_TEST) += test.o\n", encoding="utf-8")
    (kernel / "Module.symvers").write_text("0x12345678\ttest_symbol\tdrivers/test/test\tEXPORT_SYMBOL\n", encoding="utf-8")
    (kernel / "android/abi_gki_aarch64/symbols").write_text("test_symbol\n", encoding="utf-8")
    (kernel / "anykernel.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (kernel / "Image.gz").write_text("binary", encoding="utf-8")
    return kernel


def test_symbol_intelligence(tmp_path: Path) -> None:
    kernel = make_kernel(tmp_path)
    result = scan_symbols(kernel)
    assert result["unique_exported_symbol_count"] == 1
    assert result["symvers_symbol_count"] == 1
    assert result["kmi_file_count"] >= 1


def test_patch_plan_and_exports(tmp_path: Path) -> None:
    kernel = make_kernel(tmp_path)
    plan = build_patch_plan(kernel)
    assert plan["patch_count"] >= 1
    out = write_patch_plan(kernel, tmp_path / "patch")
    assert (tmp_path / "patch" / "patch-plan.md").exists()
    assert out["patch_count"] >= 1

    android_es = export_android_es(kernel, tmp_path / "android-es", device="test", brand="demo", maintainer="manish")
    rom_harbor = export_rom_harbor(kernel, tmp_path / "rom-harbor", device="test", maintainer="manish")
    droidfoundry = export_droidfoundry(kernel, tmp_path / "droidfoundry", device="test", maintainer="manish")
    assert "android-es-profile.conf" in android_es["paths"]
    assert "rom-harbor-kernel.json" in rom_harbor["paths"]
    assert "droidfoundry-kernel-handoff.json" in droidfoundry["paths"]


def test_release_check_and_ci(tmp_path: Path) -> None:
    kernel = make_kernel(tmp_path)
    release = release_check(kernel, checksum=True)
    assert release["artifact_count"] >= 1
    written = write_release_check(kernel, tmp_path / "release", checksum=True)
    assert (tmp_path / "release" / "release-check.md").exists()
    assert written["artifact_count"] >= 1

    ci = generate_ci_workflow(tmp_path / "workflow.yml")
    assert Path(ci["path"]).exists()
    assert "KernelScope Report" in Path(ci["path"]).read_text(encoding="utf-8")
