# Music Skin Overlay

Music Skin Overlay is a small Windows now-playing overlay for Spotify, Chrome, Edge, and other media sessions exposed through GSMTC.

It is intentionally viewer-only. It does not control playback. It shows what is playing in a compact, always-on-top overlay, closer to a radio now-playing card than a mini player.

## Features

- Windows GSMTC media session support
- Spotify, Chrome, Edge, current session, and auto source selection
- Compact always-on-top overlay
- System tray menu for source selection, show/hide, settings, refresh, and quit
- Separate settings window
- Thumbnail on/off
- Background opacity from 0% to 100%
- Time and progress bar on/off
- Title/detail/meta font size controls
- Title/detail/meta/accent color controls
- Smooth local interpolation for time and progress between GSMTC updates
- PyInstaller onedir executable build

## Download

For normal use, download the latest Windows zip from GitHub Releases.

After extracting the zip, run:

```text
MusicSkinOverlay\MusicSkinOverlay.exe
```

Keep the `_internal` folder next to the exe. The app will not run if only `MusicSkinOverlay.exe` is copied out by itself.

Windows SmartScreen may warn because the executable is not code-signed yet.

## Run From Source

Requirements:

- Windows 10 or newer
- Python 3.12

Install dependencies:

```powershell
py -3.12 -m pip install -r requirements.txt
```

Run with the real GSMTC provider:

```powershell
py -3.12 main.py
```

Run with dummy data for UI testing:

```powershell
py -3.12 main.py --provider dummy
```

Prefer a specific media source:

```powershell
py -3.12 main.py --provider gsmtc --source spotify
py -3.12 main.py --provider gsmtc --source chrome
```

Useful smoke tests:

```powershell
py -3.12 main.py --provider dummy --open-settings --exit-after 2
py -3.12 main.py --provider gsmtc --open-settings --exit-after 2
```

## Build

Build the Windows onedir executable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Build output:

```text
dist\MusicSkinOverlay\MusicSkinOverlay.exe
```

Create a release zip:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package_release.ps1 -Version v0.1.0
```

Package output:

```text
artifacts\MusicSkinOverlay-v0.1.0-win-x64.zip
```

## Release Flow

Recommended GitHub release flow:

1. Commit source changes.
2. Push to GitHub.
3. Create and push a version tag such as `v0.1.0`.
4. GitHub Actions builds the Windows executable and uploads the release zip.

Manual local packaging is also supported with `scripts\package_release.ps1`.

## GSMTC Probe

Inspect current GSMTC media data without launching the overlay:

```powershell
py -3.12 scripts\gsmtc_probe.py --current-only
```

List all detected media sessions:

```powershell
py -3.12 scripts\gsmtc_probe.py
```

Save a thumbnail during probing:

```powershell
py -3.12 scripts\gsmtc_probe.py --current-only --save-thumbnail
```

See [docs/GSMTC_VALIDATION.md](docs/GSMTC_VALIDATION.md) for the validation notes.

## Notes

- This app does not provide play, pause, next, previous, or seek controls.
- Thumbnail data is displayed from memory and is not saved to disk during normal use.
- If multiple media sessions exist, choose a preferred source from the tray menu or settings.
- The overlay polls GSMTC metadata in a background worker so the Qt UI thread stays responsive.
- Progress and time are interpolated locally while playing, so they can move smoothly even when GSMTC reports position less frequently.
- DirectX hooking, DLL injection, Overwolf integration, Xbox Game Bar integration, auto-update, and installers are outside the current MVP scope.

## License

MIT. See [LICENSE](LICENSE).
