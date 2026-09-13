[CmdletBinding()]
param()

# Print the application version from its single source of truth.
# Used by the release workflow to assert the pushed tag matches.

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$initFile = Join-Path $projectRoot "aero_recorder\__init__.py"

$match = Select-String -LiteralPath $initFile -Pattern '^__version__\s*=\s*"([^"]+)"'
if (-not $match) {
    throw "Could not read __version__ from $initFile"
}

Write-Output $match.Matches[0].Groups[1].Value
