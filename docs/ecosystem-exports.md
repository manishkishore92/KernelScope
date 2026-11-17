# Ecosystem Exports

KernelScope can export kernel analysis data for other maintainer tools.

## android-es

```bash
kernelscope export-android-es ./kernel/xiaomi/sweet --device sweet --brand xiaomi --maintainer manishkishore92
```

Output includes an android-es profile and a Markdown report.

## ROM Harbor

```bash
kernelscope export-rom-harbor ./kernel/xiaomi/sweet --device sweet --maintainer manishkishore92
```

Output includes release dashboard metadata and maintainer notes.

## DroidFoundry

```bash
kernelscope export-droidfoundry ./kernel/xiaomi/sweet --device sweet --maintainer manishkishore92
```

Output includes a handoff JSON and Markdown notes for device bring-up workflows.
