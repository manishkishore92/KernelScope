# Build Log Analyzer

The log analyzer scans a failed kernel build log and groups likely issues.

Supported categories include:

- Compiler error
- Missing file
- DTS / device tree
- Linker error
- Kconfig issue
- Out of memory
- Disk space
- Permission
- Toolchain

Example:

```bash
kernelscope analyze-log out/kernel-build.log
```

The analyzer is not a replacement for reading the full log. It is meant to show the most likely starting point.
