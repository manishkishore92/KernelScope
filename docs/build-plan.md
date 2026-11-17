# Build Plan Generator

KernelScope can generate a reviewable shell script for kernel builds.

Create a config:

```bash
kernelscope init-config
```

Edit `kernelscope.yml`, then generate the script:

```bash
kernelscope build-plan ./kernel/xiaomi/sweet --config kernelscope.yml --output build-kernel.sh
```

The generated script uses:

- `ARCH`
- `SUBARCH`
- defconfig
- output directory
- clang path if configured
- GCC prefix if clang is unavailable
- parallel job count

Always review the generated script before running it.
