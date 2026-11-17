# Command Reference

## scan

Summarizes the kernel tree.

```bash
kernelscope scan ./kernel/xiaomi/sweet
```

## doctor

Runs the main maintainer health check.

```bash
kernelscope doctor ./kernel/xiaomi/sweet
```

## defconfig

Works with a defconfig file or a kernel tree.

```bash
kernelscope defconfig ./kernel/xiaomi/sweet
kernelscope defconfig ./kernel/xiaomi/sweet/arch/arm64/configs/vendor/sweet_defconfig
```

## dts

Scans DTS and DTSI files.

```bash
kernelscope dts ./kernel/xiaomi/sweet
```

## analyze-log

Analyzes a kernel build log.

```bash
kernelscope analyze-log ./out/kernel-build.log
```

## report

Generates Markdown and HTML reports.

```bash
kernelscope report ./kernel/xiaomi/sweet --output kernel-report
```
