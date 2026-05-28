<#
.SYNOPSIS
    Run the leak-data-importer CLI via the project venv Python.
#>

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython  = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
    Write-Error "No .venv found. Run this first:
. .\scripts\setup.ps1"
    exit 1
}

& $VenvPython -m leak_data_importer.cli $CliArgs
exit $LASTEXITCODE