# Kernel Tree Guide

KernelScope expects a Linux or Android kernel source tree with a top-level `Makefile` and an `arch/` directory.

Common Android kernel paths include:

```text
kernel/xiaomi/sweet
kernel/oneplus/sm8250
kernel/samsung/exynos
```

A typical Android kernel tree may include:

```text
Makefile
arch/arm64/configs/*defconfig
arch/arm64/boot/dts/**/*.dts
arch/arm64/boot/dts/**/*.dtsi
drivers/
include/
scripts/
```

Some projects keep AnyKernel3 packaging in a separate repository. In that case, `kernelscope anykernel` should be run against that folder separately.
