from pathlib import Path

from kernelscope.analyzers.logs import analyze_log


def test_analyze_log_detects_missing_file(tmp_path: Path):
    log = tmp_path / "build.log"
    log.write_text("make: *** No rule to make target 'drivers/foo/bar.o'. Stop.\n", encoding="utf-8")
    result = analyze_log(log)
    assert result["finding_count"] == 1
    assert result["findings"][0]["category"] == "Missing file"
