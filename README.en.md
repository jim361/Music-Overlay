# Music Overlay

A compact Windows now-playing overlay for music and video sessions.

Music Overlay reads media sessions exposed through GSMTC (Global System Media Transport Controls) and shows what is currently playing in a small always-on-top card. It is intentionally viewer-only: no play, pause, skip, or seek controls. Think of it as a lightweight radio now-playing display, not a mini player.

[한국어](README.ko.md)

## Table Of Contents

- [Why This Exists](#why-this-exists)
- [Features](#features)
- [Download](#download)
- [Usage](#usage)
- [Settings](#settings)
- [Run From Source](#run-from-source)
- [Build](#build)
- [Notes](#notes)
- [License](#license)

## Why This Exists

When music is playing in the background, checking the current track should not mean hunting for a browser tab or opening a full player window.

Music Overlay keeps that job small:

- show the current media title in a compact overlay
- optionally appear only when the track/video changes
- stay viewer-only without playback controls
- work with Spotify, browser-based music/video, and other Windows media sessions

## Features

- Spotify, Chrome, Edge, and current Windows media session support
- Auto / Spotify / Chrome / Edge / Current source selection
- Always visible mode or show-on-media-change mode
- Album-art-only mode
- Separate toggles for thumbnail, title, details, time, and progress bar
- Pixel-based title width control for `...` truncation
- Background opacity from 0% to 100%
- Font family, font size, and color customization
- English and Korean settings UI
- System tray icon and context menus
- Windows installer and portable zip builds
- No Python installation needed for release builds

## Download

The easiest option is the setup wizard.

1. Open the [Releases](https://github.com/jim361/Music-Overlay/releases/latest) page.
2. Download `MusicOverlaySetup-...-win-x64.exe`.
3. Run the setup wizard.
4. Launch Music Overlay from the Start menu or desktop shortcut.

If you prefer a portable version:

1. Download `MusicSkinOverlay-...-win-x64.zip`.
2. Extract the zip file.
3. Run:

```text
MusicSkinOverlay\MusicSkinOverlay.exe
```

For the portable version, keep the `_internal` folder next to the exe. Do not copy only `MusicSkinOverlay.exe` out of the folder.

## Usage

- Drag the overlay to move it.
- Click or double-click the system tray icon to show or hide the overlay.
- Right-click the system tray icon to select a source, refresh, open settings, or quit.
- Right-click the overlay to refresh, select a source, open settings, or quit.
- `F5`: refresh now
- `Esc`: quit

## Settings

The settings window is split into `Basic` and `Advanced`.

### Basic

- `Language`: English / 한국어
- `Preferred source`: Auto, Spotify, Chrome, Edge, Current Windows session
- `Display mode`: always visible or show on media change
- `Show duration`: how long the overlay stays visible in auto-hide mode
- `Thumbnail`: show album art / thumbnail
- `Title`: show title
- `Details`: show artist and album
- `Time`: show time
- `Progress`: show progress bar

For album-art-only mode, keep `Thumbnail` on and turn off `Title`, `Details`, `Time`, and `Progress`.

### Advanced

- `Background opacity`: overlay background opacity
- `Overlay text width`: where long titles become `...`
- `Font`: choose from system fonts installed on the current PC
- `Title / Detail / Meta size`: font sizes
- `Title / Detail / Meta / Accent color`: colors

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

Create a release zip:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package_release.ps1 -Version v0.3.0
```

Create the setup wizard:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1 -Version v0.3.0
```

The setup wizard build requires Inno Setup 6.

## Notes

- This app does not provide play, pause, next, previous, or seek controls.
- Thumbnail data is displayed from memory and is not saved to disk during normal use.
- If multiple media sessions exist, choose a preferred source in settings.
- The executable is currently unsigned, so Windows SmartScreen may show a warning.
- Font files are not bundled. The app uses system fonts installed on the user's PC.

## License

MIT. See [LICENSE](LICENSE).
