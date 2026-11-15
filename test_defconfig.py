from pathlib import Path

from kernelscope.analyzers.defconfig import inspect_defconfig, parse_defconfig


def test_parse_defconfig(tmp_path: Path):
    path = tmp_path / "test_defconfig"
    path.write_text("CONFIG_ANDROID=y\nCONFIG_SECURITY_SELINUX=y\n# CONFIG_MODULE_SIG is not set\n", encoding="utf-8")
    config = parse_defconfig(path)
    assert config["CONFIG_ANDROID"] == "y"
    assert config["CONFIG_MODULE_SIG"] == "not set"


def test_inspect_defconfig(tmp_path: Path):
    path = tmp_path / "test_defconfig"
    path.write_text("CONFIG_ANDROID=y\nCONFIG_ANDROID_BINDER_IPC=y\nCONFIG_SECURITY_SELINUX=y\n", encoding="utf-8")
    result = inspect_defconfig(path)
    assert result["enabled"] == 3
    assert result["option_count"] == 3
