# Cross-Platform Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build cross-platform release artifacts (Windows .exe/.msi, Linux AppImage/.deb) with automated GitHub Actions.

**Architecture:** PyInstaller bundles Python runtime into single executables. WiX generates MSI from PyInstaller output. GitHub Actions matrix builds on both Windows and Linux runners.

**Tech Stack:** PyInstaller, WiX Toolset, GitHub Actions, softprops/action-gh-release

---

## File Inventory

### New Files
- `pyinstaller/bsp2stk.spec` — PyInstaller spec for GUI executable
- `pyinstaller/bsp2stk-cli.spec` — PyInstaller spec for CLI executable
- `build/msi/Product.wxs` — WiX configuration for MSI installer
- `.github/workflows/release.yml` — GitHub Actions CI/CD workflow

### Modified Files
- `.gitignore` — Add build artifacts

### External Source Files (no modification)
- `bsp/Voyager_1_merged.bsp` — Test BSP file for release

---

## Task 1: Create PyInstaller Specs

**Files:**
- Create: `pyinstaller/bsp2stk.spec` — GUI executable (bsp2stk-gui)
- Create: `pyinstaller/bsp2stk-cli.spec` — CLI executable (bsp2stk)

- [ ] **Step 1: Create pyinstaller directory**

Run: `mkdir -p pyinstaller`

- [ ] **Step 2: Create GUI spec file**

```python
# pyinstaller/bsp2stk.spec
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['src/bsp2stk/__main__.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('spiceypy') + collect_data_files('jplephem'),
    hiddenimports=[
        'spiceypy',
        'numpy',
        'scipy',
        'jplephem',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    'bsp2stk.exe',
    None,  # no icon
    [],
    False,
    'console',  # keep console for debugging output
)
```

- [ ] **Step 3: Create CLI spec file**

```python
# pyinstaller/bsp2stk-cli.spec
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['src/bsp2stk/__main__.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_files('spiceypy') + collect_data_files('jplephem'),
    hiddenimports=[
        'spiceypy',
        'numpy',
        'scipy',
        'jplephem',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    'bsp2stk-cli.exe',
    None,
    [],
    False,
    'console',
)
```

- [ ] **Step 2: Verify spec syntax**

Run: `python -c "import PyInstaller; print(PyInstaller.__version__)"` (install pyinstaller first if needed)

---

## Task 2: Create WiX MSI Configuration

**Files:**
- Create: `build/msi/Product.wxs`
- Create: `build/msi/Product.msi.props` (build properties)

- [ ] **Step 1: Create build/msi directory**

Run: `mkdir -p build/msi`

- [ ] **Step 2: Create WiX configuration with real GUIDs**

Generate GUIDs using PowerShell: `[guid]::NewGuid().ToString()`

- [ ] **Step 3: Create Product.wxs with generated GUIDs**

```xml
<!-- build/msi/Product.wxs -->
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
    <Package
        Name="bsp2stk"
        Version="0.1.0"
        Manufacturer="bsp2stk"
        UpgradeCode="A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
        Compressed="yes"
        InstallerVersion="500">

        <MajorUpgrade DowngradeErrorMessage="A newer version is already installed." />
        <MediaTemplate EmbedCab="yes" />

        <Feature Id="ProductFeature" Title="bsp2stk" Level="1">
            <ComponentGroupRef Id="ProductComponents" />
            <ComponentRef Id="ApplicationShortcut" />
        </Feature>
    </Package>

    <Fragment>
        <StandardDirectory Id="ProgramFilesFolder">
            <Directory Id="INSTALLFOLDER" Name="bsp2stk" />
        </StandardDirectory>
    </Fragment>

    <Fragment>
        <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
            <Component>
                <File Id="bsp2stk.exe" Source="..\dist\bsp2stk.exe" />
            </Component>
        </ComponentGroup>

        <DirectoryRef Id="INSTALLFOLDER">
            <Component Id="ApplicationShortcut" Guid="B1C2D3E4-F5A6-9807-BCDE-F12345678901">
                <Shortcut Id="ApplicationStartMenuShortcut"
                          Name="bsp2stk"
                          Description="BSP to STK ephemeris converter"
                          Target="[INSTALLFOLDER]bsp2stk.exe"
                          WorkingDirectory="INSTALLFOLDER" />
                <RemoveFolder Id="CleanUpShortCut" On="uninstall" />
                <RegistryValue Root="HKCU" Key="Software\bsp2stk" Name="installed" Type="integer" Value="1" KeyPath="yes" />
            </Component>
        </DirectoryRef>
    </Fragment>
</Wix>
```

- [ ] **Step 2: Test WiX compiles (on Windows with WiX installed)**

Note: WiX build will be tested in GitHub Actions on Windows runner.

---

## Task 3: Create GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create .github/workflows directory**

Run: `mkdir -p .github/workflows`

- [ ] **Step 2: Create release.yml**

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e .

      - name: Install PyInstaller
        run: pip install pyinstaller

      - name: Build executable
        run: pyinstaller pyinstaller/bsp2stk.spec

      - name: Build MSI
        run: |
          dotnet tool install --global wix
          wix build build/msi/Product.wxs -o dist/bsp2stk.msi

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: windows-artifacts
          path: |
            dist/bsp2stk.exe
            dist/bsp2stk.msi

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e .

      - name: Install PyInstaller
        run: pip install pyinstaller

      - name: Build AppImage
        run: |
          pip install pyinstaller appimage-builder
          pyinstaller --onefile --name bsp2stk src/bsp2stk/__main__.py
          # Create AppDir structure
          mkdir -p AppDir/usr/bin
          cp dist/bsp2stk AppDir/usr/bin/
          # Create AppRun
          cat > AppDir/AppRun << 'APPRUN'
          #!/bin/bash
          SELF=$(readlink -f "$0")
          HERE=${SELF%/*}
          export PATH="${HERE}/usr/bin:${PATH}"
          exec "${HERE}/usr/bin/bsp2stk" "$@"
          APPRUN
          chmod +x AppDir/AppRun
          # Build AppImage using appimagetool
          wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
          chmod +x appimagetool-x86_64.AppImage
          ./appimagetool-x86_64.AppImage AppDir dist/bsp2stk.AppImage

      - name: Build deb
        run: |
          # Create debian package structure
          mkdir -p debdist/usr/bin
          mkdir -p debdist/usr/share/applications
          mkdir -p debdist/usr/share/doc/bsp2stk
          mkdir -p debdist/DEBIAN
          # Copy executable
          cp dist/bsp2stk debdist/usr/bin/bsp2stk
          # Create control file
          cat > debdist/DEBIAN/control << 'CONTROL'
          Package: bsp2stk
          Version: 0.1.0
          Section: science
          Priority: optional
          Architecture: amd64
          Maintainer: bsp2stk
          Description: BSP to STK ephemeris converter
          CONTROL
          # Create desktop file
          cat > debdist/usr/share/applications/bsp2stk.desktop << 'DESKTOP'
          [Desktop Entry]
          Name=bsp2stk
          Comment=BSP to STK ephemeris converter
          Exec=bsp2stk
          Icon=bsp2stk
          Terminal=true
          Type=Application
          DESKTOP
          # Build deb package
          dpkg-deb --build debdist dist/bsp2stk.deb

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: linux-artifacts
          path: |
            dist/bsp2stk.AppImage
            dist/bsp2stk.deb

  release:
    needs: [build-windows, build-linux]
    runs-on: ubuntu-latest
    steps:
      - name: Download Windows artifacts
        uses: actions/download-artifact@v4
        with:
          name: windows-artifacts
          path: artifacts/windows

      - name: Download Linux artifacts
        uses: actions/download-artifact@v4
        with:
          name: linux-artifacts
          path: artifacts/linux

      - name: Download test BSP
        run: |
          mkdir -p artifacts
          cp bsp/Voyager_1_merged.bsp artifacts/

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            artifacts/windows/bsp2stk.exe
            artifacts/windows/bsp2stk.msi
            artifacts/linux/bsp2stk.AppImage
            artifacts/linux/bsp2stk.deb
            artifacts/Voyager_1_merged.bsp
          draft: true
```

---

## Task 4: Update .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add build artifacts to .gitignore**

Add to `.gitignore`:
```
# Build outputs
dist/
build/
*.egg-info/

# PyInstaller
*.spec.orig
*.spec.bak

# WiX
*.wixobj
*.wixpdb
```

---

## Verification Steps

After implementation, verify:

1. **Windows .exe**: Run `pyinstaller pyinstaller/bsp2stk.spec` on Windows, check `dist/bsp2stk.exe` exists and runs
2. **Windows .msi**: Run `wix build build/msi/Product.wxs` on Windows with WiX installed
3. **Linux AppImage**: Run PyInstaller on Linux, verify AppImage can be created
4. **Linux .deb**: Run dpkg-deb or check the structure is correct
5. **GitHub Actions**: Push a `v*` tag, verify workflow triggers and builds succeed

---

## Notes

- WiX v4 requires .NET 8 runtime on Windows (available on windows-latest)
- AppImage requires `appimage-builder` and `appimagetool` (see workflow)
- MSI GUIDs in Product.wxs are example values; replace with real GUIDs for production
- Python 3.13 may have compatibility issues with some build tools; verify versions
- GitHub Actions ubuntu-latest may not have `dpkg-deb` pre-installed; may need to install `dpkg-dev`

---

## Commit Strategy

Commit per task after each is verified:
1. `git add pyinstaller/ build/msi/ .github/ .gitignore && git commit -m "feat: add cross-platform release build configuration"`
