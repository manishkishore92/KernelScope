from pathlib import Path

from kernelscope.analyzers.scanner import scan_tree


def test_scan_tree_counts_basic_files(tmp_path: Path):
    (tmp_path / "Makefile").write_text("VERSION = 5\nPATCHLEVEL = 10\nSUBLEVEL = 0\n", encoding="utf-8")
    cfg = tmp_path / "arch" / "arm64" / "configs"
    cfg.mkdir(parents=True)
    (cfg / "vendor_test_defconfig").write_text("CONFIG_ANDROID=y\n", encoding="utf-8")
    dts = tmp_path / "arch" / "arm64" / "boot" / "dts" / "vendor"
    dts.mkdir(parents=True)
    (dts / "test.dts").write_text("/dts-v1/;\n", encoding="utf-8")

    result = scan_tree(tmp_path)
    assert result["kernel_version"] == "5.10.0"
    assert result["defconfig_count"] == 1
    assert result["dts_count"] == 1
