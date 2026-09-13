[CmdletBinding()]
param(
    [string]$Version,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not $Version) {
    $initFile = Join-Path $projectRoot "aero_recorder\__init__.py"
    $match = Select-String -LiteralPath $initFile -Pattern '^__version__\s*=\s*"([^"]+)"'
    if (-not $match) {
        throw "Could not read __version__ from $initFile"
    }
    $Version = $match.Matches[0].Groups[1].Value
}
Write-Host "Building AeroRecorder $Version"
$venvDirectory = if ($env:AERORECORDER_BUILD_VENV) {
    $env:AERORECORDER_BUILD_VENV
} else {
    Join-Path $projectRoot ".venv"
}
$ffmpegPath = Join-Path $projectRoot "tools\ffmpeg.exe"

if (-not (Test-Path -LiteralPath $ffmpegPath)) {
    throw "FFmpeg is missing. Run scripts\get-ffmpeg.ps1 before building."
}

$configuredPython = $env:AERORECORDER_PYTHON
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($configuredPython -and (Test-Path -LiteralPath $configuredPython)) {
    $pythonExecutable = $configuredPython
} elseif ($pythonCommand) {
    $pythonExecutable = $pythonCommand.Source
} else {
    $commonPython = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe","$env:ProgramFiles\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($commonPython) {
        $pythonExecutable = $commonPython.FullName
    } else {
        $launcher = Get-Command py -ErrorAction SilentlyContinue
        if (-not $launcher) {
            throw "Python 3 was not found."
        }
        $pythonExecutable = $launcher.Source
    }
}

if (-not (Test-Path -LiteralPath $venvDirectory)) {
    if ((Split-Path -Leaf $pythonExecutable) -ieq "py.exe") {
        & $pythonExecutable -3 -m venv $venvDirectory
    } else {
        & $pythonExecutable -m venv $venvDirectory
    }
}

$venvPython = Join-Path $venvDirectory "Scripts\python.exe"
& $venvPython -m pip install --disable-pip-version-check -r (Join-Path $projectRoot "requirements-dev.txt")
& $venvPython (Join-Path $projectRoot "scripts\create_icon.py")
Push-Location $projectRoot
try {
    & $venvPython -m PyInstaller --noconfirm --clean "AeroRecorder.spec"
} finally {
    Pop-Location
}

$portableFolder = Join-Path $projectRoot "dist\AeroRecorder"
$portableMarker = Join-Path $portableFolder "portable.flag"
$portableArchive = Join-Path $projectRoot "dist\AeroRecorder-Portable-$Version.zip"
Set-Content -LiteralPath $portableMarker -Value "AeroRecorder portable mode" -Encoding ascii
if (Test-Path -LiteralPath $portableArchive) {
    Remove-Item -LiteralPath $portableArchive -Force
}
Compress-Archive -Path (Join-Path $portableFolder "*") -DestinationPath $portableArchive -CompressionLevel Optimal
Write-Host "Portable ZIP created in $portableArchive"

if ($SkipInstaller) {
    Write-Host "Installer skipped by request. Portable build is in dist\AeroRecorder"
    return
}

$innoCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$innoCompiler = $innoCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $innoCompiler) {
    throw "Inno Setup 6 was not found. Install it, or pass -SkipInstaller for a portable-only build."
}

& $innoCompiler "/DMyAppVersion=$Version" (Join-Path $projectRoot "installer\AeroRecorder.iss")
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}
Write-Host "Installer created in installer\output\AeroRecorder-Setup-$Version.exe"
