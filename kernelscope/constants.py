from __future__ import annotations

IGNORED_DIRS = {
    ".git",
    ".repo",
    ".gradle",
    ".idea",
    ".vscode",
    ".pytest_cache",
    "__pycache__",
    "out",
    "build",
    "dist",
    "node_modules",
}

ANDROID_KERNEL_CONFIGS = {
    "CONFIG_ANDROID": "Android core support",
    "CONFIG_ANDROID_BINDER_IPC": "Binder IPC",
    "CONFIG_ANDROID_BINDERFS": "Binder filesystem",
    "CONFIG_ASHMEM": "Android ashmem legacy support",
    "CONFIG_ION": "ION memory allocator",
    "CONFIG_DMABUF_HEAPS": "DMA-BUF heaps",
    "CONFIG_CGROUPS": "Control groups",
    "CONFIG_NAMESPACES": "Namespaces",
    "CONFIG_PSI": "Pressure stall information",
    "CONFIG_PM_WAKELOCKS": "Kernel wakelocks",
    "CONFIG_USB_CONFIGFS_F_ADB": "ADB configfs function",
}

SECURITY_CONFIGS = {
    "CONFIG_SECURITY": "Linux security framework",
    "CONFIG_SECURITY_SELINUX": "SELinux support",
    "CONFIG_SECURITY_SELINUX_BOOTPARAM": "SELinux boot parameter",
    "CONFIG_DM_VERITY": "dm-verity support",
    "CONFIG_MODULE_SIG": "Kernel module signing",
    "CONFIG_MODULE_SIG_FORCE": "Force signed modules",
    "CONFIG_STRICT_KERNEL_RWX": "Strict kernel memory permissions",
    "CONFIG_STRICT_MODULE_RWX": "Strict module memory permissions",
    "CONFIG_RANDOMIZE_BASE": "Kernel address space layout randomization",
    "CONFIG_STACKPROTECTOR": "Stack protector",
    "CONFIG_STACKPROTECTOR_STRONG": "Strong stack protector",
    "CONFIG_HARDENED_USERCOPY": "Hardened usercopy",
    "CONFIG_FORTIFY_SOURCE": "Fortify source",
    "CONFIG_INIT_STACK_ALL_ZERO": "Initialize stack variables",
}

LOG_PATTERNS = [
    {
        "category": "Compiler error",
        "severity": "high",
        "needles": ["fatal error:", "error: unknown type name", "error: use of undeclared identifier"],
        "suggestion": "Check the missing include, changed API, or incompatible kernel branch/toolchain.",
    },
    {
        "category": "Missing file",
        "severity": "high",
        "needles": ["No rule to make target", "No such file or directory", "file not found"],
        "suggestion": "Verify paths in Makefile/Kbuild, generated headers, DTS includes, and vendor module references.",
    },
    {
        "category": "DTC / device tree",
        "severity": "high",
        "needles": ["dtc", "DTC", "device tree", "syntax error"],
        "suggestion": "Inspect DTS/DTSI syntax, include order, labels, phandles, and board overlay changes.",
    },
    {
        "category": "Linker error",
        "severity": "high",
        "needles": ["undefined reference", "ld.lld", "vmlinux.o", "relocation"],
        "suggestion": "Check disabled config symbols, missing object files, wrong compiler flags, or incompatible source changes.",
    },
    {
        "category": "Kconfig issue",
        "severity": "medium",
        "needles": ["recursive dependency", "symbol value", "Kconfig"],
        "suggestion": "Review Kconfig dependency chains and defconfig options introduced by the branch or patch.",
    },
    {
        "category": "Out of memory",
        "severity": "high",
        "needles": ["Killed", "out of memory", "Cannot allocate memory"],
        "suggestion": "Lower parallel jobs, add swap, or build on a machine with more RAM.",
    },
    {
        "category": "Disk space",
        "severity": "high",
        "needles": ["No space left on device", "Disk quota exceeded"],
        "suggestion": "Free build output, ccache, or temporary files before rebuilding.",
    },
    {
        "category": "Permission",
        "severity": "medium",
        "needles": ["Permission denied", "Operation not permitted"],
        "suggestion": "Check executable bits, file ownership, mounted filesystem permissions, and script paths.",
    },
    {
        "category": "Toolchain",
        "severity": "medium",
        "needles": ["clang:", "gcc:", "unsupported option", "unrecognized command line option"],
        "suggestion": "Use the expected Android clang/GCC version and confirm CROSS_COMPILE/LLVM settings.",
    },
]

TOOLCHAIN_TOOLS = [
    "git",
    "make",
    "python3",
    "perl",
    "bc",
    "bison",
    "flex",
    "openssl",
    "clang",
    "gcc",
    "ld.lld",
    "dtc",
    "ccache",
    "lz4",
    "lzop",
]
