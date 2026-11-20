# Patch Plan

The patch plan command turns KernelScope findings into a safe review list.

```bash
kernelscope patch-plan ./kernel/xiaomi/sweet --output kernel-patch-plan
```

Generated files:

```text
kernel-patch-plan/
├── patch-plan.md
└── patch-plan.json
```

The patch plan does not edit the kernel tree. It groups findings into review areas such as defconfig, DTS, build-system, symbols, packaging, and release readiness.

Use it before manually creating commits or before asking another maintainer to review the tree.
