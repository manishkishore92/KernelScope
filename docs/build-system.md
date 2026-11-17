# Build System Detection

`kernelscope build-system` detects common Android kernel build styles.

```bash
kernelscope build-system ./kernel/xiaomi/sweet
```

Detected styles can include Makefile builds, Android `build.config` / `build.sh`, Kleaf/Bazel, custom shell scripts, and AnyKernel3 packaging.

Use `build-plan-full` to generate reviewable helper scripts.
