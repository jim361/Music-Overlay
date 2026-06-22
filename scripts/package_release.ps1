param(
    [string]$Version = "dev",
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if ($Build) {
    & (Join-Path $PSScriptRoot "build_exe.ps1")
}

$distDir = Join-Path $root "dist\MusicSkinOverlay"
$exePath = Join-Path $distDir "MusicSkinOverlay.exe"
if (-not (Test-Path $exePath)) {
    throw "Package failed: build output not found at $exePath. Run scripts\build_exe.ps1 first."
}

$artifactsDir = Join-Path $root "artifacts"
New-Item -ItemType Directory -Path $artifactsDir -Force | Out-Null

$safeVersion = $Version -replace "[^A-Za-z0-9._-]", "-"
$zipPath = Join-Path $artifactsDir "MusicSkinOverlay-$safeVersion-win-x64.zip"

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -LiteralPath $distDir -DestinationPath $zipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "Package complete:"
Write-Host "  $zipPath"
