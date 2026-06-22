# Music Overlay

[한국어](README.ko.md)

Music Overlay is a small Windows now-playing overlay for media sessions exposed through GSMTC (Global System Media Transport Controls).

It is intentionally viewer-only. It does not control playback. It shows what is playing in a compact always-on-top overlay, closer to a radio now-playing card than a mini player.

## Features

- Windows GSMTC media session support
- Spotify, Chrome, Edge, current session, and auto source selection
- Compact always-on-top overlay
- System tray menu
- Separate settings window
- Thumbnail on/off
- Background opacity from 0% to 100%
- Time and progress bar on/off
- Title/detail/meta font size controls
- Title/detail/meta/accent color controls
- Smooth local interpolation for time and progress between GSMTC updates

## Download And Run

1. Open the [Releases](https://github.com/jim361/Music-Overlay/releases/latest) page.
2. Download `MusicSkinOverlay-...-win-x64.zip`.
3. Extract the zip file.
4. Run:

```text
MusicSkinOverlay\MusicSkinOverlay.exe
```

Important:

- Do not copy only `MusicSkinOverlay.exe` out of the folder.
- The `_internal` folder must stay next to the exe.
- Windows SmartScreen may warn because the executable is not code-signed yet.

## Usage

- Drag the overlay to move it.
- Click or double-click the system tray icon to show or hide the overlay.
- Right-click the system tray icon to select a source or open settings.
- Right-click the overlay to refresh, select a source, open settings, or quit.
- `F5`: refresh now
- `Esc`: quit

## Settings

The settings window supports:

- Preferred source
- Show thumbnail
- Background opacity
- Show time
- Show progress bar
- Title size
- Detail size
- Meta size
- Title color
- Detail color
- Meta color
- Accent color
- Reset Position

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

## Build

Build the Windows executable folder:

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

## Notes

- This app does not provide play, pause, next, previous, or seek controls.
- Thumbnail data is displayed from memory and is not saved to disk during normal use.
- If multiple media sessions exist, choose a preferred source from settings.
- The executable is currently unsigned.

## License

MIT. See [LICENSE](LICENSE).
