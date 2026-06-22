# GSMTC Validation

Use this before building or changing the overlay provider. The goal is to
confirm whether Windows GSMTC can provide enough metadata and controls for the
MVP.

## Setup

Install Python for Windows if `py --version` says no Python is installed.

Current local setup:

```text
Python 3.12.10
winsdk 1.0.0b10
```

Then install the probe dependency:

```powershell
py -3.12 -m pip install -r requirements-gsmtc.txt
```

## One-Shot Probe

Start playback in Spotify, then run:

```powershell
py -3.12 scripts\gsmtc_probe.py --current-only
```

For thumbnail extraction:

```powershell
py -3.12 scripts\gsmtc_probe.py --current-only --save-thumbnail
```

For change observation while skipping tracks:

```powershell
py -3.12 scripts\gsmtc_probe.py --current-only --watch --interval 1
```

To inspect all available sessions:

```powershell
py -3.12 scripts\gsmtc_probe.py
```

## What To Record

| Target | Title | Artist | Artwork | Position | Duration | Play/Pause | Prev/Next | Seek | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Spotify desktop | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Verified on 2026-06-22 |
| Spotify web Chrome |  |  |  |  |  |  |  |  | Not separately verified yet |
| Spotify web Edge |  |  |  |  |  |  |  |  |  |
| Chrome media session | Yes | Yes | Yes | Yes | Yes | Yes | Partial | Yes | Verified with YouTube-like session |
| YouTube Music web Chrome | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested | Premium unavailable |
| YouTube Music PWA | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested | Premium unavailable |

## Verified Samples

Chrome:

```text
source:   Chrome
status:   playing
time:     3:26 / 10:27
controls: play=False, pause=True, toggle=True, prev=False, next=False, seek=True
artwork:  yes
```

Spotify desktop:

```text
source:   SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify
album:    VULTURES 1
status:   playing
controls: play=False, pause=True, toggle=True, prev=True, next=True, seek=True
artwork:  yes
thumbnail: probe-output\session_0_thumbnail.png
```

## Decision Rule

- If Spotify desktop and browser sessions expose title, artist, duration,
  position, and playback status, continue with GSMTC as the first provider.
- If controls are inconsistent but metadata is stable, build the MVP as a
  display-first overlay and keep playback controls optional.
- If GSMTC metadata is unreliable, keep the provider interface but consider a
  Spotify-specific fallback later.

## Current Decision

GSMTC is accepted as the MVP provider. The first app build should focus on
Spotify desktop, while keeping source selection generic enough for Chrome,
Edge, and future YouTube Music/PWA tests.
