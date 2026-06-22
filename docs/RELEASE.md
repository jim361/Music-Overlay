# Release Guide

This project ships Windows builds as GitHub Release assets.

Recommended user download:

- `MusicOverlaySetup-<version>-win-x64.exe`: setup wizard

Portable fallback:

- `MusicSkinOverlay-<version>-win-x64.zip`: portable onedir package

## Versioning

Use semantic version tags:

```text
v0.1.0
v0.2.0
v1.0.0
```

## Local Build

Build the executable folder:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Create the portable release zip:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package_release.ps1 -Version v0.2.0
```

Expected output:

```text
artifacts\MusicSkinOverlay-v0.2.0-win-x64.zip
```

Create the setup wizard:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1 -Version v0.2.0
```

Expected output:

```text
artifacts\MusicOverlaySetup-v0.2.0-win-x64.exe
```

Installer builds require Inno Setup 6.

## GitHub Actions Release

After changes are pushed to GitHub:

```powershell
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

The `Windows Build` workflow will:

1. Install Python 3.12 dependencies.
2. Build the PyInstaller onedir app.
3. Package `dist\MusicSkinOverlay` as a zip.
4. Install Inno Setup.
5. Build the setup wizard.
6. Upload both artifacts.
7. Create a GitHub Release for `v*` tags.

## User Notes

Tell users to prefer the setup wizard:

```text
MusicOverlaySetup-v0.2.0-win-x64.exe
```

For portable use, tell users to extract the zip and run:

```text
MusicSkinOverlay\MusicSkinOverlay.exe
```

The `_internal` folder must stay next to the exe for the portable zip.

Python does not need to be installed separately for either release asset.

The executable is currently unsigned, so Windows SmartScreen may show a warning.
