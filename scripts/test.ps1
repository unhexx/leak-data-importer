<#
.SYNOPSIS
    Run pytest via the project's virtual environment Python.
#>

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython  = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
    Write-Error "No .venv found. Run this first:
. .\scripts\setup.ps1"
    exit 1
}

Write-Host "Running tests via $VenvPython ..." -ForegroundColor Cyan
& $VenvPython -m pytest $PytestArgs
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "
✓ All tests passed." -ForegroundColor Green
} else {
    Write-Host "
✗ Tests failed with exit code $exitCode." -ForegroundColor Red
}

exit $exitCode