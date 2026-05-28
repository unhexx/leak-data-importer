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
Write-Host "Target venv (REQUIRED): $VenvPath" -ForegroundColor White

# Robust base Python discovery (reject Inkscape etc.)
function Find-ReliablePython {
    $bad = @('inkscape','git\mingw','msys64','windowsapps')
    $c = [System.Collections.Generic.List[string]]::new()

    # py launcher
    foreach ($v in @('-3.12','-3.11','-3.10','')) {
        try {
            $e = & py $v -c "import sys; print(sys.executable)" 2>$null
            if ($e -and (Test-Path $e)) { $c.Add([string]$e) }
        } catch {}
    }

    # common locations
    $roots = @(
        "C:\Python312","C:\Python311","C:\Python310",
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:ProgramFiles\Python312"
    )
    foreach ($r in $roots) { $e = Join-Path $r 'python.exe'; if (Test-Path $e) { $c.Add($e) } }

    # PATH filtered
    foreach ($d in ($env:PATH -split ';')) {
        $e = Join-Path $d 'python.exe'
        if (Test-Path $e) { $c.Add($e) }
    }

    $seen = @{}
    foreach ($exe in $c) {
        $l = $exe.ToLowerInvariant()
        if ($seen[$l]) { continue }; $seen[$l] = $true
        $isBad = $false; foreach ($b in $bad) { if ($l -like "*$b*") { $isBad=$true; break } }
        if ($isBad) { continue }
        try {
            $ver = & $exe --version 2>&1
            if ($ver -match "Python 3\.(1[0-9])" -and (& $exe -c "import venv;print('ok')" 2>&1) -match "ok") {
                return $exe
            }
        } catch {}
    }
    return $null
}

$basePy = Find-ReliablePython
if (-not $basePy) {
    Write-Error @"
No usable Python 3.10+ found (current "python" is likely Inkscape or broken).

Install clean Python 3.12 from python.org and re-run this script.
Target venv must be: $VenvPath
"@
    exit 1
}
Write-Host "Base Python: $basePy" -ForegroundColor DarkGray

if (-not (Test-Path $VenvPath)) {
    Write-Host 'Creating .venv ...' -ForegroundColor Yellow
    & $basePy -m venv $VenvPath
}

if (Test-Path $Activate) {
    Write-Host 'Activating virtual environment...' -ForegroundColor Green
    . $Activate
} else {
    Write-Warning "Activate script not found: $Activate"
}

Write-Host 'Upgrading pip (via venv python)...' -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip --quiet

Write-Host 'Installing project in editable mode with [dev] extras...' -ForegroundColor Yellow
& $VenvPython -m pip install -e "$ProjectRoot.[dev]"

Write-Host ''
Write-Host '✓ Done. Virtual environment is now active in this shell.' -ForegroundColor Green
Write-Host "  Direct python path (use in agents): $VenvPython" -ForegroundColor DarkGray
Write-Host ''
Write-Host 'Next useful commands:' -ForegroundColor DarkGray
Write-Host '  .\scripts\test.ps1           # run tests' -ForegroundColor DarkGray
Write-Host '  .\scripts\lint.ps1           # lint + type check' -ForegroundColor DarkGray
Write-Host '  .\scripts\run.ps1 --help     # CLI' -ForegroundColor DarkGray
Write-Host '  .\scripts\streamlit.ps1      # Streamlit UI' -ForegroundColor DarkGray
Write-Host ''
Write-Host 'To deactivate later:  deactivate' -ForegroundColor DarkGray
Write-Host ''
