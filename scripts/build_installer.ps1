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

$distExe = Join-Path $root "dist\MusicSkinOverlay\MusicSkinOverlay.exe"
if (-not (Test-Path $distExe)) {
    throw "Installer build failed: build output not found at $distExe. Run scripts\build_exe.ps1 first."
}

$isccCommand = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
$isccPath = if ($isccCommand) { $isccCommand.Source } else { $null }
if (-not $isccPath) {
    $candidatePaths = @(
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
    )
    foreach ($candidate in $candidatePaths) {
        if ($candidate -and (Test-Path $candidate)) {
            $isccPath = $candidate
            break
        }
    }
}

if (-not $isccPath) {
    throw "Inno Setup 6 was not found. Install it with: winget install JRSoftware.InnoSetup"
}

$artifactsDir = Join-Path $root "artifacts"
New-Item -ItemType Directory -Path $artifactsDir -Force | Out-Null

$safeVersion = $Version -replace "[^A-Za-z0-9._-]", "-"
$issPath = Join-Path $root "packaging\installer.iss"

& $isccPath "/DAppVersion=$safeVersion" $issPath

$installerPath = Join-Path $artifactsDir "MusicOverlaySetup-$safeVersion-win-x64.exe"
if (-not (Test-Path $installerPath)) {
    throw "Installer build failed: $installerPath was not created."
}

Write-Host ""
Write-Host "Installer complete:"
Write-Host "  $installerPath"
