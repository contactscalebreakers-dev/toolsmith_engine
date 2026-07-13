# SB Toolsmith Pro - Deployment Guide

## Overview

This guide covers building, packaging, and deploying SB Toolsmith Pro for Windows 11.

## Prerequisites

### Development Environment
- Python 3.9+
- PySide6
- PyInstaller
- NSIS (for installer creation)

### Installation

```bash
# Install build dependencies
pip install -r requirements.txt
pip install pyinstaller nuitka

# Optional: NSIS for Windows installer
# Download from https://nsis.sourceforge.io/
```

## Build Process

### 1. Development Build

```bash
# Run directly from source
python main_integrated.py
```

### 2. Optimized Executable Build

```bash
# Build optimized executable
python scripts/build_optimized.py --clean --optimize

# Build single-file executable
python scripts/build_optimized.py --onefile

# Build with installer
python scripts/build_optimized.py --installer

# Create deployment package
python scripts/build_optimized.py --package
```

### 3. Build Options

| Option | Description |
|--------|-------------|
| `--clean` | Clean previous build artifacts |
| `--optimize` | Optimize Python code before build |
| `--onefile` | Build single executable file |
| `--installer` | Create Windows installer (requires NSIS) |
| `--package` | Create deployment package |

## Output Artifacts

### Directory Structure

```
dist/
├── SBToolsmithPro/          # Executable and dependencies
│   ├── SBToolsmithPro.exe
│   ├── PySide6/
│   ├── config/
│   └── ...
└── SBToolsmithPro.exe       # Single file (if --onefile)

deployment/
├── SBToolsmithPro.exe       # Packaged executable
├── README.md
├── ARCHITECTURE.md
└── PHASE_8_INTEGRATION.md
```

## Deployment Methods

### Method 1: Direct Distribution

1. Build executable: `python scripts/build_optimized.py`
2. Distribute `dist/SBToolsmithPro/` folder
3. Users run `SBToolsmithPro.exe`

### Method 2: Single File Executable

1. Build single file: `python scripts/build_optimized.py --onefile`
2. Distribute `dist/SBToolsmithPro.exe`
3. Users run single executable

### Method 3: Windows Installer

1. Build installer: `python scripts/build_optimized.py --installer`
2. Distribute `SBToolsmithPro-1.0.0-setup.exe`
3. Users run installer, creates Start Menu shortcuts

### Method 4: Deployment Package

1. Create package: `python scripts/build_optimized.py --package`
2. Distribute `deployment/` folder
3. Users extract and run `SBToolsmithPro.exe`

## Performance Optimization

### Build-Time Optimization

```bash
# Compile Python to bytecode
python scripts/build_optimized.py --optimize

# Use UPX compression (if available)
pyinstaller --upx-dir=/path/to/upx ...

# Strip debug symbols
pyinstaller --strip ...
```

### Runtime Optimization

1. **Lazy Loading**: Modules loaded on-demand
2. **Caching**: Compiled bytecode cached
3. **Memory**: Minimal startup memory footprint
4. **Startup**: ~2-3 seconds on modern hardware

### Size Optimization

| Build Type | Size |
|-----------|------|
| Single File | ~120-150 MB |
| Directory | ~80-100 MB |
| Compressed | ~40-50 MB |

## System Requirements

### Minimum
- Windows 10 or later
- 2 GB RAM
- 500 MB disk space
- .NET Framework 4.5+ (for some features)

### Recommended
- Windows 11
- 4 GB RAM
- 1 GB disk space
- SSD for faster startup

## Installation

### From Installer

1. Download `SBToolsmithPro-1.0.0-setup.exe`
2. Run installer
3. Follow wizard
4. Launch from Start Menu

### From Executable

1. Download `SBToolsmithPro.exe`
2. Run directly or create shortcut
3. Application starts immediately

### From Directory

1. Extract `dist/SBToolsmithPro/` folder
2. Run `SBToolsmithPro.exe`
3. Create shortcut if desired

## Configuration

### First Launch

1. Application creates `~/.sb-toolsmith/` directory
2. Default settings created
3. Configuration UI available in Settings menu

### Settings Location

```
C:\Users\<username>\.sb-toolsmith\
├── config/
│   └── settings.json
├── graphs/
│   ├── graph1.json
│   └── ...
├── venvs/
│   ├── venv_1/
│   └── ...
└── snapshots/
    ├── snapshot_1/
    └── ...
```

## Troubleshooting

### Application Won't Start

1. Check Windows Event Viewer for errors
2. Verify Python dependencies installed
3. Check disk space (minimum 500 MB)
4. Try running from command line for error output

### Performance Issues

1. Check available RAM
2. Disable AI features if not needed
3. Reduce graph complexity
4. Check disk I/O performance

### Missing Dependencies

1. Reinstall from installer
2. Check `requirements.txt` for missing packages
3. Verify PySide6 installation

## Updates

### Version Updates

1. Download new `SBToolsmithPro.exe`
2. Close running application
3. Replace executable
4. Settings and graphs preserved

### Backup

```bash
# Backup settings and graphs
xcopy %USERPROFILE%\.sb-toolsmith backup /E /I

# Restore from backup
xcopy backup %USERPROFILE%\.sb-toolsmith /E /I
```

## Uninstallation

### From Installer

1. Control Panel → Programs → Uninstall a program
2. Select "SB Toolsmith Pro"
3. Click Uninstall

### Manual Uninstallation

1. Delete application folder
2. Delete shortcuts (Start Menu, Desktop)
3. Delete `~/.sb-toolsmith/` if desired

## Distribution

### GitHub Release

```bash
# Create release
gh release create v1.0.0 \
  dist/SBToolsmithPro.exe \
  SBToolsmithPro-1.0.0-setup.exe \
  --title "SB Toolsmith Pro v1.0.0"
```

### Website Distribution

1. Upload to website
2. Create download page
3. Include system requirements
4. Provide installation instructions

## Monitoring

### Logs

```
~/.sb-toolsmith/logs/
├── app.log
├── error.log
└── debug.log
```

### Diagnostics

1. Launch with `--debug` flag
2. Check logs for errors
3. Verify configuration

## Support

- **Documentation**: [docs.sb-toolsmith.dev](https://docs.sb-toolsmith.dev)
- **Issues**: [GitHub Issues](https://github.com/sb-toolsmith/pro/issues)
- **Community**: [Discord](https://discord.gg/sb-toolsmith)

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0
