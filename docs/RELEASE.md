# Release Guide

This project ships Windows builds as GitHub Release zip files.

## Versioning

Use semantic version tags:

```text
v0.1.0
v0.2.0
v1.0.0
```

For the current MVP, `v0.1.0` is a good first release tag.

## Local Build

Build the executable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Create the release zip:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package_release.ps1 -Version v0.1.0
```

Expected output:

```text
artifacts\MusicSkinOverlay-v0.1.0-win-x64.zip
```

## GitHub Actions Release

After the repository is pushed to GitHub:

```powershell
git tag v0.1.0
git push origin main
git push origin v0.1.0
```

The `Windows Build` workflow will:

1. Install Python 3.12 dependencies.
2. Build the PyInstaller onedir app.
3. Package `dist\MusicSkinOverlay`.
4. Upload a zip artifact.
5. Create a GitHub Release for `v*` tags.

## Manual Release Upload

If the workflow is not used, create a release on GitHub and upload:

```text
artifacts\MusicSkinOverlay-v0.1.0-win-x64.zip
```

## User Notes

Tell users to extract the zip and run:

```text
MusicSkinOverlay\MusicSkinOverlay.exe
```

The `_internal` folder must stay next to the exe.

The executable is currently unsigned, so Windows SmartScreen may show a warning.
