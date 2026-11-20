# GKI and KMI Checks

`kernelscope gki-check` scans a kernel tree for GKI/KMI-related hints.

```bash
kernelscope gki-check ./kernel/xiaomi/sweet
```

It looks for GKI defconfigs, Android build configs, ABI symbol lists, KMI symbol lists, protected modules lists, module output hints, and vendor module folders.

The command does not certify a tree as GKI compliant. It points maintainers to files and missing review areas.
