# CI Export

KernelScope can generate an optional GitHub Actions workflow file.

```bash
kernelscope ci-export --output kernelscope-report.yml
```

The generated workflow installs KernelScope and creates an intelligence report artifact. The command only creates a workflow file when requested; the repository does not include CI clutter by default.
