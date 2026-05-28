<#
.SYNOPSIS
    Setup Python environment for leak-data-importer on Windows PowerShell.

.DESCRIPTION
    Creates .venv if missing, activates it in the current session,
    and installs the package in editable mode with dev dependencies.

.IMPORTANT
    You MUST run this script with dot-sourcing (the dot + space):

        cd X:\LocalRepo\leak-data-importer
        . .\scripts\setup.ps1

    Otherwise the venv activation will not affect your current shell.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath    = Join-Path $ProjectRoot '.venv'
$Activate    = Join-Path $VenvPath 'Scripts\Activate.ps1'
$VenvPython  = Join-Path $VenvPath 'Scripts\python.exe'

Write-Host ''
Write-Host '=== leak-data-importer :: environment setup (PowerShell) ===' -ForegroundColor Cyan

if (-not (Test-Path $VenvPath)) {
    Write-Host 'Creating .venv ...' -ForegroundColor Yellow
    python -m venv $VenvPath
}

if (Test-Path $Activate) {
    Write-Host 'Activating virtual environment...' -ForegroundColor Green
    . $Activate
} else {
    Write-Warning "Activate script not found: $Activate"
}

Write-Host 'Upgrading pip...' -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip --quiet

Write-Host 'Installing project in editable mode with [dev] extras...' -ForegroundColor Yellow
& $VenvPython -m pip install -e "$ProjectRoot.[dev]"

Write-Host ''
Write-Host '✓ Done. Virtual environment is now active in this shell.' -ForegroundColor Green
Write-Host ''
Write-Host 'Next useful commands:' -ForegroundColor DarkGray
Write-Host '  .\scripts\test.ps1           # run tests' -ForegroundColor DarkGray
Write-Host '  .\scripts\lint.ps1           # lint + type check' -ForegroundColor DarkGray
Write-Host '  .\scripts\run.ps1 --help     # CLI' -ForegroundColor DarkGray
Write-Host '  .\scripts\streamlit.ps1      # Streamlit UI' -ForegroundColor DarkGray
Write-Host ''
Write-Host 'To deactivate later:  deactivate' -ForegroundColor DarkGray
Write-Host ''
