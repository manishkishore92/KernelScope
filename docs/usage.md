# KernelScope Usage

KernelScope is used from the terminal.

```bash
kernelscope --help
```

The most useful first command is:

```bash
kernelscope doctor ./kernel-source
```

This runs the main checks and prints findings with suggestions.

## JSON

Use `--json` when you want machine-readable output.

```bash
kernelscope scan ./kernel-source --json
```

Use `--output` to write JSON to disk.

```bash
kernelscope doctor ./kernel-source --json --output doctor.json
```
