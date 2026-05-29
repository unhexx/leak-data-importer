# setup_env.ps1
# Robust environment bootstrap for autonomous agentic development loops.
# Always ensures a local Python venv exists and is up-to-date with requirements.
# Designed to be called by the Orchestrator at the start of every cycle.
#
# CRITICAL: This script NEVER trusts bare "python" from PATH.
# It will find a reliable base Python (rejecting Inkscape etc.) only to create/repair .venv,
# then uses the venv's python.exe for everything else.

param(
    [string]$PythonVersion = "3.11",
    [string]$VenvDir = ".venv",
    [string]$RequirementsFile = "requirements.txt"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== Agentic Loop Environment Bootstrap ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray
Write-Host "REQUIRED venv location: $ProjectRoot\$VenvDir" -ForegroundColor White

# ============================================
# Same robust Python discovery used by Agent-Init.ps1
# ============================================

function Find-ReliablePython {
    [CmdletBinding()]
    param()

    $badSubstrings = @(
        'inkscape',
        'git\mingw',
        'git\usr\bin',
        'msys64',
        'windowsapps',
        'windows defender'
    )

    $candidates = [System.Collections.Generic.List[string]]::new()

    # 1. py launcher first
    $pyVersions = @('-3.12', '-3.11', '-3.10', '-3.9', '')
    foreach ($ver in $pyVersions) {
        try {
            $exe = & py $ver -c "import sys; print(sys.executable)" 2>$null
            if ($exe -and (Test-Path $exe -ErrorAction SilentlyContinue)) {
                $candidates.Add([string]$exe)
            }
        } catch {}
    }

    # 2. Known good locations
    $userProfile  = $env:USERPROFILE
    $programFiles = ${env:ProgramFiles}
    $localAppData = $env:LOCALAPPDATA

    $roots = @(
        "C:\Python312","C:\Python311","C:\Python310",
        (Join-Path $programFiles "Python312"),
        (Join-Path $programFiles "Python311"),
        (Join-Path $localAppData "Programs\Python\Python312"),
        (Join-Path $localAppData "Programs\Python\Python311"),
        (Join-Path $userProfile  "AppData\Local\Programs\Python\Python312"),
        (Join-Path $userProfile  "AppData\Local\Programs\Python\Python311")
    ) | Where-Object { $_ }

    foreach ($r in $roots) {
        $exe = Join-Path $r "python.exe"
        if (Test-Path $exe) { $candidates.Add($exe) }
    }

    # 3. PATH (filtered)
    foreach ($dir in ($env:PATH -split ';')) {
        if (-not $dir) { continue }
        $exe = Join-Path $dir "python.exe"
        if (Test-Path $exe) { $candidates.Add($exe) }
    }

    $seen = @{}
    foreach ($exe in $candidates) {
        $l = $exe.ToLowerInvariant()
        if ($seen.ContainsKey($l)) { continue }
        $seen[$l] = $true

        $bad = $false
        foreach ($b in $badSubstrings) { if ($l -like "*$b*") { $bad = $true; break } }
        if ($bad) { continue }

        try {
            $v = & $exe --version 2>&1
            if ($v -match "Python 3\.(1[0-9])") {
                $t = & $exe -c "import venv; print('ok')" 2>&1
                if ($t -match "ok") { return $exe }
            }
        } catch {}
    }
    return $null
}

# 1. Locate RELIABLE base Python (only for venv creation)
Write-Host "`n[1/7] Locating reliable Python (never trust PATH on this machine)..." -ForegroundColor Yellow

$basePython = Find-ReliablePython

if (-not $basePython) {
    $cur = $null; try { $cur = (& python --version 2>&1) } catch {}
    $src = $null; try { $src = (Get-Command python).Source } catch {}

    Write-Error @"
No reliable Python found capable of creating venvs.

Current PATH python: $cur → $src

This project REQUIRES the environment at:
  $ProjectRoot\$VenvDir

Fix: Install clean Python 3.12 from python.org (with py launcher) and/or add Windows Defender exclusion for the project folder.
"@
    exit 1
}

Write-Host "  Reliable base Python: $basePython" -ForegroundColor Green

# 2. Ensure the REQUIRED venv exists (repair if broken)
Write-Host "`n[2/7] Ensuring virtual environment at $ProjectRoot\$VenvDir ..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot $VenvDir
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
$venvPython   = Join-Path $venvPath "Scripts\python.exe"

$needsRepair = $false

if (Test-Path $venvPath) {
    if (-not (Test-Path $venvPython) -or -not (Test-Path $activateScript)) {
        Write-Host "  Venv exists but is broken. Repairing..." -ForegroundColor DarkYellow
        $needsRepair = $true
    } else {
        try {
            $v = & $venvPython --version 2>&1
            Write-Host "  Existing venv OK ($v)" -ForegroundColor Green
        } catch {
            $needsRepair = $true
        }
    }
} else {
    $needsRepair = $true
}

if ($needsRepair) {
    if (Test-Path $venvPath) {
        Remove-Item $venvPath -Recurse -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 300
    }
    Write-Host "  Creating venv using reliable base Python..." -ForegroundColor Yellow
    & $basePython -m venv $venvPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
        Write-Error "Failed to create/repair venv at $venvPath using $basePython"
        exit 1
    }
    Write-Host "  Venv created/repaired." -ForegroundColor Green
}

if (-not (Test-Path $venvPython)) {
    Write-Error "venv python.exe still missing: $venvPython"
    exit 1
}

# 3. Activate (best effort for interactive use)
Write-Host "`n[3/7] Activating environment..." -ForegroundColor Yellow
if (Test-Path $activateScript) {
    try {
        . $activateScript
    } catch {}
}

# From this point EVERY python/pip call MUST go through the venv python directly
Write-Host "  All python work will use: $venvPython" -ForegroundColor DarkGray

# 4. Upgrade pip
Write-Host "`n[4/7] Upgrading pip..." -ForegroundColor Yellow

function Invoke-VenvPip {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $venvPython -m pip @Arguments 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $old
    return $code
}

$upExit = Invoke-VenvPip @('install', '--upgrade', 'pip', '--quiet')
if ($upExit -eq 0) {
    Write-Host "  pip upgraded." -ForegroundColor Green
} else {
    Write-Host "  Warning: pip upgrade returned $upExit (continuing)." -ForegroundColor DarkYellow
}

# 5. Install dependencies (prefer pyproject.toml)
Write-Host "`n[5/7] Installing project dependencies..." -ForegroundColor Yellow
$installed = $false

if (Test-Path (Join-Path $ProjectRoot "pyproject.toml")) {
    Write-Host "  Using pyproject.toml..." -ForegroundColor Gray
    $instExit = Invoke-VenvPip @('install', '-e', "$ProjectRoot.[dev]", '--quiet')
    if ($instExit -eq 0) {
        $installed = $true
        Write-Host "  Installed from pyproject.toml." -ForegroundColor Green
    } else {
        Write-Host "  Warning: pyproject install returned $instExit (continuing)." -ForegroundColor DarkYellow
    }
}

if (-not $installed -and (Test-Path (Join-Path $ProjectRoot $RequirementsFile))) {
    Write-Host "  Falling back to $RequirementsFile..." -ForegroundColor Gray
    $instExit = Invoke-VenvPip @('install', '-r', (Join-Path $ProjectRoot $RequirementsFile), '--quiet')
    if ($instExit -eq 0) {
        $installed = $true
        Write-Host "  Dependencies installed from $RequirementsFile." -ForegroundColor Green
    } else {
        Write-Host "  Warning: requirements install returned $instExit." -ForegroundColor DarkYellow
    }
}

if (-not $installed) {
    Write-Host "  ⚠ No pyproject.toml or $RequirementsFile found." -ForegroundColor DarkYellow
}

# 6. Verify critical packages (non-fatal)
Write-Host "`n[6/7] Verifying key packages..." -ForegroundColor Yellow
$critical = @("pydantic", "charset-normalizer")

foreach ($pkg in $critical) {
    try {
        $ver = & $venvPython -c "import importlib.metadata; print(importlib.metadata.version('$pkg'))" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $pkg $ver" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ $pkg not installed" -ForegroundColor DarkYellow
        }
    } catch {
        Write-Host "  ⚠ Could not verify $pkg" -ForegroundColor DarkYellow
    }
}

# 7. Git hygiene
Write-Host "`n[7/7] Git status check..." -ForegroundColor Yellow
try {
    $branch = git rev-parse --abbrev-ref HEAD 2>&1
    Write-Host "  Current branch: $branch" -ForegroundColor Gray
    $status = git status --porcelain 2>&1
    if ($status) {
        Write-Host "  Uncommitted changes present." -ForegroundColor DarkYellow
    } else {
        Write-Host "  Working tree clean." -ForegroundColor Green
    }
} catch {
    Write-Host "  Git not available or not a repo." -ForegroundColor DarkYellow
}

Write-Host "`n=== Environment ready for agentic loop ===" -ForegroundColor Cyan
Write-Host "REQUIRED venv: $venvPath" -ForegroundColor White
Write-Host "Direct python: $venvPython" -ForegroundColor White
Write-Host "To reactivate in a new shell: . .\$VenvDir\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "Agent must call this script (or use $venvPython directly) at the start of every major cycle." -ForegroundColor Gray