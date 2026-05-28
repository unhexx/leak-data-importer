<#
.SYNOPSIS
    Robust initialization script for Blackbox + MiniMax2.5 agentic development in VSCode.

.DESCRIPTION
    Prepares a reliable local Python virtual environment and can generate
    a ready-to-use starter prompt for Blackbox.

    Key improvements:
    - Automatically creates or repairs broken .venv
    - Clear, step-by-step messages with status
    - Auto-detects task from TODO.md or TASK_SPECIFICATION.md
#>

[CmdletBinding()]
param(
    [string]$TaskDescription,
    [string]$TaskSpecFile = "TASK_SPECIFICATION.md",
    [string]$OutputFile,
    [switch]$GeneratePromptOnly,
    [int]$MaxTaskLength = 2800
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Force UTF-8 everywhere possible (console + pipeline).
# Strongly recommended on Russian Windows where the system codepage is often CP1251.
# Wrapped in try/catch because [Console]::OutputEncoding can fail or be meaningless
# in non-interactive / redirected sessions (Blackbox, agents, CI, etc.).
try {
    $OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # Non-interactive environment — safe to ignore.
}

function Get-AutoTaskDescription {
    param([int]$MaxLength = 2800)

    $candidates = @(
        (Join-Path $ProjectRoot "TASK_SPECIFICATION.md"),
        (Join-Path $ProjectRoot "TODO.md")
    )

    foreach ($file in $candidates) {
        if (Test-Path $file) {
            try {
                # Use explicit UTF-8 via .NET to avoid Windows-1251 mojibake on Russian machines
                # (Get-Content without -Encoding uses the system ANSI codepage, which is deadly for UTF-8 files)
                $raw = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
                if ($raw.Length -gt $MaxLength) {
                    $raw = $raw.Substring(0, $MaxLength) + "`n... (truncated)"
                }
                Write-Host "  Auto-detected task from: $(Split-Path $file -Leaf)" -ForegroundColor Green
                return $raw.Trim()
            } catch {}
        }
    }
    return $null
}

function Generate-AgentStarterPrompt {
    param([string]$Task, [string]$SpecFile = "TASK_SPECIFICATION.md")

    $lines = @(
        "We are starting an autonomous agentic development loop using the template in agentic_loop_template/.",
        "",
        "**Current Task:**",
        $Task,
        "",
        "**Instructions:**",
        "",
        "1. First, ensure the local Python environment is ready by running:",
        "   powershell -ExecutionPolicy Bypass -File .\agentic_loop_template\Agent-Init.ps1",
        "",
        "2. Activate the virtual environment:",
        "   . .\.venv\Scripts\Activate.ps1",
        "",
        "3. Read in this order:",
        "   - docs/agentic_loop/README.md",
        "   - docs/agentic_loop/SYSTEM_PROMPT.md",
        "   - docs/agentic_loop/Agent-Init.md",
        "   - $SpecFile",
        "",
        "4. Start as ORCHESTRATOR according to the SYSTEM_PROMPT.",
        "",
        "Rules:",
        "- Write all git commits in natural Russian, as a real human developer.",
        "- Never mention AI, LLM, agent, MiniMax, Grok, Claude, etc. in commit messages.",
        "- Always work inside the local .venv."
    )

    return ($lines -join "`r`n")
}

# ============================================
# Robust Python discovery (critical when PATH is polluted by Inkscape, Git, etc.)
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
        'windows defender',
        'program files (x86)\microsoft visual studio'
    )

    $candidates = [System.Collections.Generic.List[string]]::new()

    # 1. Windows Python Launcher "py" (highest priority - designed exactly for this situation)
    $pyVersions = @('-3.12', '-3.11', '-3.10', '-3.9', '')
    foreach ($ver in $pyVersions) {
        try {
            $exe = & py $ver -c "import sys; print(sys.executable)" 2>$null
            if ($exe -and (Test-Path $exe -ErrorAction SilentlyContinue)) {
                $candidates.Add([string]$exe)
            }
        } catch {}
    }

    # 2. Explicit well-known locations (bypass PATH completely)
    $userProfile   = $env:USERPROFILE
    $programFiles  = ${env:ProgramFiles}
    $localAppData  = $env:LOCALAPPDATA

    $searchRoots = @(
        "C:\Python312", "C:\Python311", "C:\Python310", "C:\Python39", "C:\Python38",
        (Join-Path $programFiles  "Python312"),
        (Join-Path $programFiles  "Python311"),
        (Join-Path $programFiles  "Python310"),
        (Join-Path $localAppData  "Programs\Python\Python312"),
        (Join-Path $localAppData  "Programs\Python\Python311"),
        (Join-Path $localAppData  "Programs\Python\Python310"),
        (Join-Path $userProfile   "AppData\Local\Programs\Python\Python312"),
        (Join-Path $userProfile   "AppData\Local\Programs\Python\Python311"),
        (Join-Path $userProfile   "AppData\Local\Programs\Python\Python310")
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($root in $searchRoots) {
        $exe = Join-Path $root "python.exe"
        if (Test-Path $exe) { $candidates.Add($exe) }
    }

    # 3. Walk PATH but we will filter aggressively later
    $pathDirs = ($env:PATH -split ';') | Where-Object { $_.Trim() }
    foreach ($dir in $pathDirs) {
        $exe = Join-Path $dir "python.exe"
        if (Test-Path $exe) { $candidates.Add($exe) }
    }

    # Deduplicate + filter bad + validate
    $seen = @{}
    foreach ($exe in $candidates) {
        $lower = $exe.ToLowerInvariant()
        if ($seen.ContainsKey($lower)) { continue }
        $seen[$lower] = $true

        $isBad = $false
        foreach ($bad in $badSubstrings) {
            if ($lower -like "*$bad*") { $isBad = $true; break }
        }
        if ($isBad) { continue }

        try {
            $ver = & $exe --version 2>&1
            if ($ver -match "Python 3\.(1[0-9]|[2-9][0-9])") {
                # Must be able to create venvs
                $venvTest = & $exe -c "import venv; print('venv_ok')" 2>&1
                if ($venvTest -match "venv_ok") {
                    return $exe
                }
            }
        } catch {}
    }

    return $null
}

# ============================================
# Main Logic - Robust Venv Handling
# ============================================

Write-Host "=== Agentic Loop Environment Initialization ===" -ForegroundColor Cyan
Write-Host "Reminder: Before starting work, the agent must complete the Pre-Flight Checklist in SYSTEM_PROMPT.md (version 2.1)." -ForegroundColor DarkGray
Write-Host "Project: $ProjectRoot" -ForegroundColor Gray

# 1. Locate a RELIABLE base Python (never trust bare "python" on this machine)
Write-Host "`n[1/6] Locating reliable Python (rejecting Inkscape and other junk)..." -ForegroundColor Yellow

$basePython = Find-ReliablePython

if (-not $basePython) {
    $currentPy = $null
    try { $currentPy = (& python --version 2>&1) } catch {}
    $currentSrc = $null
    try { $currentSrc = (Get-Command python -ErrorAction SilentlyContinue).Source } catch {}

    Write-Error @"
No reliable Python 3.10+ found that is capable of creating a proper virtual environment.

Current "python" resolves to:
  Version: $currentPy
  Path   : $currentSrc

This machine has a polluted PATH (common when Inkscape or Git Bash is installed).

REQUIRED: The project MUST use exactly this environment:
  $ProjectRoot\.venv

Recommended fixes (try in order):

1. Install official Python 3.12 from https://www.python.org/downloads/
   (IMPORTANT: check "Add python.exe to PATH" + "Install Python Launcher (py.exe)")

2. If you already have Python installed somewhere, run the launcher explicitly:
   py -3.12 -m venv .venv

3. Add an exclusion for the whole project in Windows Defender (helps with .venv creation):
   Windows Security → Virus & threat protection → Manage settings → Exclusions
   → Add folder: $ProjectRoot

4. Run this script from an elevated (Administrator) PowerShell.

After installing a clean Python, re-run:
  powershell -ExecutionPolicy Bypass -File .\agentic_loop_template\Agent-Init.ps1
"@
    exit 1
}

Write-Host "  Using reliable base Python: $basePython" -ForegroundColor Green

# 2. Robust venv handling — always create/repair the EXACT required .venv
Write-Host "`n[2/6] Ensuring virtual environment at $ProjectRoot\.venv ..." -ForegroundColor Yellow

$venvPath = Join-Path $ProjectRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
$venvPython   = Join-Path $venvPath "Scripts\python.exe"

$needsRecreate = $false

if (Test-Path $venvPath) {
    if (-not (Test-Path $activateScript) -or -not (Test-Path $venvPython)) {
        Write-Host "  Existing .venv is broken (missing Activate.ps1 or python.exe). Recreating..." -ForegroundColor DarkYellow
        $needsRecreate = $true
    } else {
        try {
            $ver = & $venvPython --version 2>&1
            Write-Host "  Existing venv is valid ($ver)" -ForegroundColor Green
        } catch {
            Write-Host "  Existing venv Python is broken. Recreating..." -ForegroundColor DarkYellow
            $needsRecreate = $true
        }
    }
} else {
    $needsRecreate = $true
}

if ($needsRecreate) {
    if (Test-Path $venvPath) {
        Write-Host "  Removing old/broken .venv..." -ForegroundColor DarkYellow
        Remove-Item $venvPath -Recurse -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 400
    }

    Write-Host "  Creating new virtual environment using reliable Python..." -ForegroundColor Yellow
    & $basePython -m venv $venvPath
    $createExit = $LASTEXITCODE

    if ($createExit -ne 0 -or -not (Test-Path $venvPython)) {
        Write-Error @"
Failed to create a working virtual environment at $venvPath

Base Python used: $basePython
Exit code: $createExit

Common causes on this machine:
- Windows Defender / antivirus is quarantining files inside .venv the moment they appear
- The base Python itself is partially broken or blocked

Immediate actions:
1. Add a permanent exclusion:
   Windows Security → Virus & threat protection → Manage settings → Exclusions
   → Add folder: $ProjectRoot\.venv   (and preferably the whole $ProjectRoot)

2. Try creating manually in an elevated shell:
   & "$basePython" -m venv .venv

3. Then re-run this script.

The agentic loop REQUIRES the environment at: $ProjectRoot\.venv
"@
        exit 1
    }

    # Wait for Activate.ps1 (antivirus delay protection)
    Write-Host "  Waiting for activation script..." -ForegroundColor Gray
    $maxWait = 18
    $waited  = 0
    $interval = 450

    while (-not (Test-Path $activateScript) -and $waited -lt $maxWait) {
        Start-Sleep -Milliseconds $interval
        $waited += ($interval / 1000.0)
    }

    if (-not (Test-Path $activateScript)) {
        Write-Error @"
Activate.ps1 did not appear after venv creation (waited $maxWait seconds).

This is a classic Windows Defender + Inkscape-PATH combination problem.

Please:
1. Add exclusion for $ProjectRoot\.venv
2. Delete the partial .venv folder manually
3. Re-run this script

Required environment location: $ProjectRoot\.venv
"@
        exit 1
    }

    Write-Host "  Virtual environment created successfully (took ~$([math]::Round($waited,1))s)." -ForegroundColor Green
}

# From this point we ALWAYS use the venv python directly
if (-not (Test-Path $venvPython)) {
    Write-Error "venv python.exe is missing after creation: $venvPython"
    exit 1
}

# 3. Activate (for interactive humans). Agents should prefer $venvPython directly.
Write-Host "`n[3/6] Activating virtual environment (for current shell)..." -ForegroundColor Yellow

if (-not (Test-Path $activateScript)) {
    Write-Error "Activation script is missing."
    exit 1
}

try {
    . $activateScript

    $currentPy = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($currentPy -and $currentPy -like "*\.venv\*") {
        Write-Host "  Virtual environment activated in this shell." -ForegroundColor Green
    } else {
        Write-Host "  Note: Activation did not override PATH in this session (common in agents)." -ForegroundColor DarkYellow
        Write-Host "  All further python calls in this script will use the full venv path." -ForegroundColor DarkYellow
    }
} catch {
    Write-Warning "Activation threw an error (non-fatal for agents): $_"
}

Write-Host "  → From now on this script uses: $venvPython" -ForegroundColor DarkGray

# 4. Upgrade pip + install dependencies — ALWAYS via the venv python directly
# We must be extremely tolerant to stderr warnings from pip (NativeCommandError under $ErrorActionPreference=Stop)
Write-Host "`n[4/6] Upgrading pip and installing dependencies..." -ForegroundColor Yellow

function Invoke-VenvPip {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $venvPython -m pip @Arguments 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $old
    return $code
}

$pipUpgradeExit = Invoke-VenvPip @('install', '--upgrade', 'pip', '--quiet')
if ($pipUpgradeExit -eq 0) {
    Write-Host "  pip upgraded." -ForegroundColor Green
} else {
    Write-Host "  Warning: pip upgrade returned exit code $pipUpgradeExit (continuing anyway)." -ForegroundColor DarkYellow
}

if (Test-Path (Join-Path $ProjectRoot "pyproject.toml")) {
    $instExit = Invoke-VenvPip @('install', '-e', "$ProjectRoot.[dev]", '--quiet')
    if ($instExit -eq 0) {
        Write-Host "  Dependencies installed from pyproject.toml." -ForegroundColor Green
    } else {
        Write-Host "  Warning: dependency install returned $instExit (may still work)." -ForegroundColor DarkYellow
    }
} elseif (Test-Path (Join-Path $ProjectRoot "requirements.txt")) {
    $instExit = Invoke-VenvPip @('install', '-r', (Join-Path $ProjectRoot "requirements.txt"), '--quiet')
    if ($instExit -eq 0) {
        Write-Host "  Dependencies installed from requirements.txt." -ForegroundColor Green
    } else {
        Write-Host "  Warning: dependency install returned $instExit." -ForegroundColor DarkYellow
    }
} else {
    Write-Host "  No dependency file found. Skipping installation." -ForegroundColor DarkYellow
}

# 5. Set helpful environment variables
Write-Host "`n[5/6] Setting agent-friendly environment variables..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("POSH_BASH_CHAINING_NONINTERACTIVE", "1", "User")
$env:POSH_BASH_CHAINING_NONINTERACTIVE = "1"
Write-Host "  Variables set for non-interactive sessions." -ForegroundColor Green

# 6. Prompt generation
Write-Host "`n[6/6] Checking for task description..." -ForegroundColor Yellow

$finalTask = $TaskDescription
if (-not $finalTask) {
    $finalTask = Get-AutoTaskDescription -MaxLength $MaxTaskLength
}

if ($finalTask) {
    $prompt = Generate-AgentStarterPrompt -Task $finalTask -SpecFile $TaskSpecFile

    if ($OutputFile) {
        $out = if ([System.IO.Path]::IsPathRooted($OutputFile)) { $OutputFile } else { Join-Path $ProjectRoot $OutputFile }
        # Write as clean UTF-8 (no BOM) — better for pasting into agents/LLMs
        [System.IO.File]::WriteAllText($out, $prompt, [System.Text.Encoding]::UTF8)
        Write-Host "  Starter prompt saved to: $out" -ForegroundColor Green
    }

    Write-Host "`n=== Ready-to-use prompt for Blackbox ===" -ForegroundColor Yellow
    Write-Host $prompt
    Write-Host "========================================" -ForegroundColor Yellow
} else {
    Write-Host "  No task description found automatically." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "=== Agentic Loop Environment Ready ===" -ForegroundColor Green
Write-Host "REQUIRED venv location : $venvPath" -ForegroundColor White
Write-Host "Direct python executable: $venvPython" -ForegroundColor White
Write-Host "Use this in all agent steps: & `"$venvPython`" -m ..." -ForegroundColor DarkGray
Write-Host "=============================================" -ForegroundColor Green