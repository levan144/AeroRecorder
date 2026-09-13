[CmdletBinding()]
param(
    [switch]$Force
)

# Fetch the exact FFmpeg build pinned in ffmpeg.lock.json.
#
# Every download is verified against the pinned SHA-256 and deleted on
# mismatch. An unverified binary is never allowed to proceed. Verified builds
# are cached by hash so repeated builds and CI runs do not re-download.

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsDirectory = Join-Path $projectRoot "tools"
$lockPath = Join-Path $projectRoot "ffmpeg.lock.json"

if (-not (Test-Path -LiteralPath $lockPath)) {
    throw "ffmpeg.lock.json was not found at $lockPath"
}

$lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json
foreach ($field in @("version", "url", "sha256", "archive_member")) {
    if (-not $lock.$field) {
        throw "ffmpeg.lock.json is missing the required field '$field'"
    }
}
if ($lock.sha256 -notmatch '^[0-9a-f]{64}$') {
    throw "ffmpeg.lock.json: sha256 must be 64 lowercase hexadecimal characters"
}
if (-not $lock.url.StartsWith("https://")) {
    throw "ffmpeg.lock.json: url must use https"
}
$isArchive = $true
if ($lock.PSObject.Properties.Name -contains "is_archive") {
    $isArchive = [bool]$lock.is_archive
}

$shortHash = $lock.sha256.Substring(0, 12)
$cacheRoot = Join-Path $env:LOCALAPPDATA "AeroRecorder\ffmpeg-cache"
$cacheDirectory = Join-Path $cacheRoot $lock.sha256
$cachedFfmpeg = Join-Path $cacheDirectory "ffmpeg.exe"
$cachedLicense = Join-Path $cacheDirectory "FFMPEG-LICENSE.txt"

New-Item -ItemType Directory -Force -Path $toolsDirectory | Out-Null

function Copy-FromCache {
    Copy-Item -LiteralPath $cachedFfmpeg -Destination (Join-Path $toolsDirectory "ffmpeg.exe") -Force
    if (Test-Path -LiteralPath $cachedLicense) {
        Copy-Item -LiteralPath $cachedLicense -Destination (Join-Path $toolsDirectory "FFMPEG-LICENSE.txt") -Force
    }
    Write-Host "FFmpeg $($lock.version) ($($lock.build)) is ready in $toolsDirectory"
}

if ((Test-Path -LiteralPath $cachedFfmpeg) -and -not $Force) {
    Write-Host "Using the cached FFmpeg build $shortHash"
    Copy-FromCache
    return
}

$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$archivePath = Join-Path $tempRoot "aerorecorder-ffmpeg-$shortHash.download"
$extractDirectory = Join-Path $tempRoot "aerorecorder-ffmpeg-extract-$shortHash"

if (-not ([System.IO.Path]::GetFullPath($extractDirectory)).StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to extract outside the system temporary directory."
}
if (Test-Path -LiteralPath $extractDirectory) {
    Remove-Item -LiteralPath $extractDirectory -Recurse -Force
}

try {
    Write-Host "Downloading FFmpeg $($lock.version) from $($lock.url)"
    Invoke-WebRequest -Uri $lock.url -OutFile $archivePath -UseBasicParsing

    $actual = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $lock.sha256) {
        Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue
        throw @"
FFmpeg checksum verification FAILED. The download was deleted.

  expected: $($lock.sha256)
  actual:   $actual

Do not proceed. Either the download was corrupted, or the pinned artifact
changed, which must never happen for an immutable release URL.
"@
    }
    Write-Host "Checksum verified: $actual"

    New-Item -ItemType Directory -Force -Path $cacheDirectory | Out-Null

    if (-not $isArchive) {
        # A trimmed build may be published as a bare executable.
        Copy-Item -LiteralPath $archivePath -Destination $cachedFfmpeg -Force
        if ($lock.license_url) {
            Invoke-WebRequest -Uri $lock.license_url -OutFile $cachedLicense -UseBasicParsing
        }
        Copy-FromCache
        return
    }

    $zipPath = "$archivePath.zip"
    Move-Item -LiteralPath $archivePath -Destination $zipPath -Force
    $archivePath = $zipPath
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDirectory -Force

    $member = Join-Path $extractDirectory ($lock.archive_member -replace "/", "\")
    if (-not (Test-Path -LiteralPath $member)) {
        throw "The archive did not contain the expected member '$($lock.archive_member)'"
    }
    Copy-Item -LiteralPath $member -Destination $cachedFfmpeg -Force

    $licenseCopied = $false
    if ($lock.license_member) {
        $licensePath = Join-Path $extractDirectory ($lock.license_member -replace "/", "\")
        if (Test-Path -LiteralPath $licensePath) {
            Copy-Item -LiteralPath $licensePath -Destination $cachedLicense -Force
            $licenseCopied = $true
        }
    }
    if (-not $licenseCopied) {
        $license = Get-ChildItem -LiteralPath $extractDirectory -File -Recurse | Where-Object {
            $_.Name -match "^(LICENSE|COPYING)(\..+)?$"
        } | Select-Object -First 1
        if ($license) {
            Copy-Item -LiteralPath $license.FullName -Destination $cachedLicense -Force
            $licenseCopied = $true
        }
    }
    if (-not $licenseCopied) {
        Write-Warning "No LICENSE file was found in the FFmpeg archive. GPL compliance requires one."
    }

    Copy-FromCache
}
finally {
    Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $extractDirectory) {
        Remove-Item -LiteralPath $extractDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}
