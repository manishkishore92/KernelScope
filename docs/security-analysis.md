# Security Analysis

`kernelscope security` checks defconfigs for Android and kernel security options.

```bash
kernelscope security ./kernel/xiaomi/sweet
```

The audit reviews SELinux, dm-verity, strict memory permissions, KASLR, stack protector, hardened usercopy, fortify source, module signing, and debug-related options.

Some options are branch-specific. KernelScope reports findings for maintainer review instead of making unsafe automatic changes.
