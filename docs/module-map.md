# Module Map

`kernelscope module-map` scans `.ko` files, Makefiles, Kbuild files, `modules.order`, and `Module.symvers`.

```bash
kernelscope module-map ./kernel/xiaomi/sweet
```

The output groups module hints by hardware area so maintainers can review vendor module expectations and packaging paths.
