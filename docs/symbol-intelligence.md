# Symbol Intelligence

KernelScope can inspect exported symbols and symbol-list related files in Android kernel trees.

```bash
kernelscope symbols ./kernel/xiaomi/sweet
```

The command checks for:

- `Module.symvers`
- `vmlinux.symvers`
- KMI/ABI symbol list files
- `EXPORT_SYMBOL` usage in source files
- Duplicate exported symbol names
- Top modules from symvers entries

This is useful before changing exported APIs, rebasing vendor driver trees, or reviewing a GKI/KMI-sensitive branch.

JSON output is available:

```bash
kernelscope symbols ./kernel/xiaomi/sweet --json
```
