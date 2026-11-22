# Recommendation Plan

The recommendation command creates a prioritized maintainer checklist from KernelScope findings.

```bash
kernelscope recommend ./kernel/xiaomi/sweet
```

It groups suggestions into:

- Immediate checks
- Before-build actions
- Before-release actions
- Automation workflow notes

For automation:

```bash
kernelscope recommend ./kernel/xiaomi/sweet --json
```
