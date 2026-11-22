# Release Check

The release checker reviews a kernel output or AnyKernel3 package folder before publishing.

```bash
kernelscope release-check ./kernel/xiaomi/sweet --package ./AnyKernel3 --output release-check --checksum
```

It detects common release artifacts:

- Kernel images
- DTBO images
- Vendor boot images
- Flashable ZIP files
- Kernel modules

With `--checksum`, KernelScope calculates SHA-256 values for detected artifacts and writes `SHA256SUMS` when possible.

Use this before uploading standalone kernel ZIPs or attaching artifacts to ROM release notes.
