<#
.SYNOPSIS
    Lint + type check using ruff and mypy via the project venv.
#>

[CmdletBinding()]
param(
    [switch]$Fix
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython  = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
    Write-Error "No .venv found. Run this first:
. .\scripts\setup.ps1"
    exit 1
}

Write-Host "=== Code quality checks (ruff + mypy) ===" -ForegroundColor Cyan

$ruffArgs = @('check', '.')
if ($Fix) { $ruffArgs += '--fix' }

Write-Host "
[1/2] ruff check ..." -ForegroundColor Yellow
& $VenvPython -m ruff $ruffArgs
$ruffExit = $LASTEXITCODE

Write-Host "
[2/2] ruff format --check ..." -ForegroundColor Yellow
& $VenvPython -m ruff format --check .
$formatExit = $LASTEXITCODE

Write-Host "
[3/3] mypy src ..." -ForegroundColor Yellow
& $VenvPython -m mypy src
$mypyExit = $LASTEXITCODE

$failed = ($ruffExit -ne 0) -or ($formatExit -ne 0) -or ($mypyExit -ne 0)

if (-not $failed) {
    Write-Host "
✓ Lint and type checks passed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "
✗ Issues found." -ForegroundColor Red
    if ($Fix) {
        Write-Host "  (Some fixes were applied by ruff)" -ForegroundColor DarkGray
    } else {
        Write-Host "  Tip: run  .\scripts\lint.ps1 -Fix" -ForegroundColor DarkGray
    }
    exit 1
}