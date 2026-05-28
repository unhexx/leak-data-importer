<#
.SYNOPSIS
    Launch the Streamlit control UI.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython  = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$AppPath     = Join-Path $ProjectRoot 'app\streamlit_app.py'

if (-not (Test-Path $VenvPython)) {
    Write-Error "No .venv found. Run this first:
. .\scripts\setup.ps1"
    exit 1
}
if (-not (Test-Path $AppPath)) {
    Write-Error "App not found: $AppPath"
    exit 1
}

Write-Host "Starting Streamlit UI..." -ForegroundColor Cyan
& $VenvPython -m streamlit run $AppPath
exit $LASTEXITCODE