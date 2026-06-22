$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$pythonExe = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"

function Invoke-Python {
    if (Test-Path $pythonExe) {
        & $pythonExe @args
    } else {
        py -3.12 @args
    }
}

Invoke-Python -m pip install -r requirements.txt
Invoke-Python -m pip install -r requirements-build.txt
Invoke-Python -m PyInstaller packaging\music_skin_overlay.spec --noconfirm --clean

$exePath = Join-Path $root "dist\MusicSkinOverlay\MusicSkinOverlay.exe"
if (-not (Test-Path $exePath)) {
    throw "Build failed: $exePath was not created."
}

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\MusicSkinOverlay\MusicSkinOverlay.exe"
