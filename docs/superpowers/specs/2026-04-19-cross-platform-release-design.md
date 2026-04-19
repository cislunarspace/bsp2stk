# Cross-Platform Release Design

## Overview

Package bsp2stk as standalone executables and installers for Windows and Linux, published as GitHub Releases with automated CI/CD.

## Goals

- Users can download and run the application without installing Python
- Support both portable (single-file) and installed versions
- Include test BSP file for users to verify installation

## Release Artifacts

| File | Platform | Description |
|------|----------|-------------|
| `bsp2stk.exe` | Windows | Single-file executable (PyInstaller) |
| `bsp2stk.msi` | Windows | MSI installer (WiX) |
| `bsp2stk.AppImage` | Linux | Single-file executable (AppImage) |
| `bsp2stk.deb` | Linux | Debian package |
| `Voyager_1_merged.bsp` | All | Test BSP file (separate download) |

## Build Configuration

### PyInstaller (Windows .exe)
- Single-file mode with console and GUI entry points
- No bundling of test data files

### WiX (Windows .msi)
- Per-user installation by default
- Start menu shortcuts
- Uninstaller entry in Add/Remove Programs

### AppImage (Linux)
- Single-file, no installation required
- Desktop integration optional

### Debian Package (.deb)
- Standard dpkg installation
- Menu entry and icon integration

## GitHub Actions Workflow

Trigger: On git tag starting with `v`

Matrix strategy:
- Windows: `windows-latest` → builds .exe and .msi
- Linux: `ubuntu-latest` → builds AppImage and .deb

Artifacts published to GitHub Release automatically via `softprops/action-gh-release`

## File Structure

```
bsp2stk/
├── pyinstaller/
│   ├── bsp2stk.spec          # PyInstaller spec
│   └── console.spec           # CLI entry point
├── build/
│   └── msi/
│       └── Product.wxs        # WiX configuration
├── .github/
│   └── workflows/
│       └── release.yml        # CI/CD workflow
└── tests/
    └── Voyager_1_merged.bsp   # Test file (copied to release)
```

## Versioning

- Version follows git tags: `v*.*.*`
- Python version: >= 3.13
- Build dependencies not bundled in final artifacts

## Implementation Tasks

1. Add PyInstaller spec files for Windows builds
2. Add WiX configuration for MSI generation
3. Create GitHub Actions workflow for cross-platform builds
4. Configure release automation to attach artifacts
5. Test build outputs on Windows and Linux runners
