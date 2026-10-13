#!/usr/bin/env bash
set -euo pipefail

python -m compileall -q kernelscope
kernelscope --help >/dev/null
pytest -q
