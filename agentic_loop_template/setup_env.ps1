# setup_env.ps1
# Robust environment bootstrap for autonomous agentic development loops.
# Always ensures a local Python venv exists and is up-to-date with requirements.
# Designed to be called by the Orchestrator at the start of every cycle.
#
# Usage (from project root):
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup_env.ps1

param(
    [string]$PythonVersion = "3.11",
    [string]$VenvDir = ".venv",
    [string]$RequirementsFile = "requirements.txt"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== Agentic Loop Environment Bootstrap ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray

# 1. Locate Python
Write-Host "`n[1/7] Locating Python $PythonVersion..." -ForegroundColor Yellow
$pythonExe = $null
$candidates = @("python", "python3", "py")
foreach ($candidate in $candidates) {
    try {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python $PythonVersion") {
            $pythonExe = $candidate
            Write-Host "  ✓ Found: $ver via $candidate" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonExe) {
    Write-Error "Python $PythonVersion not found in PATH. Agent cannot continue without it."
    exit 1
}

# 2. Create venv if missing (idempotent)
Write-Host "`n[2/7] Ensuring virtual environment in $VenvDir..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot $VenvDir
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "  Creating venv..." -ForegroundColor DarkYellow
    & $pythonExe -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment."
        exit 1
    }
    Write-Host "  ✓ Venv created." -ForegroundColor Green
} else {
    Write-Host "  ✓ Venv already exists." -ForegroundColor Green
}

# 3. Activate
Write-Host "`n[3/7] Activating environment..." -ForegroundColor Yellow
if (-not (Test-Path $activateScript)) {
    Write-Error "Activation script missing: $activateScript"
    exit 1
}
. $activateScript
Write-Host "  ✓ Environment activated." -ForegroundColor Green

# 4. Upgrade pip
Write-Host "`n[4/7] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "  ✓ pip upgraded." -ForegroundColor Green

# 5. Install dependencies (prefer pyproject.toml, fallback to requirements.txt)
Write-Host "`n[5/7] Installing project dependencies..." -ForegroundColor Yellow
$installed = $false

if (Test-Path (Join-Path $ProjectRoot "pyproject.toml")) {
    Write-Host "  Using pyproject.toml..." -ForegroundColor Gray
    python -m pip install -e "$ProjectRoot.[dev]" --quiet
    if ($LASTEXITCODE -eq 0) {
        $installed = $true
        Write-Host "  ✓ Installed from pyproject.toml (including dev extras)." -ForegroundColor Green
    }
}

if (-not $installed -and (Test-Path (Join-Path $ProjectRoot $RequirementsFile))) {
    Write-Host "  Falling back to $RequirementsFile..." -ForegroundColor Gray
    python -m pip install -r (Join-Path $ProjectRoot $RequirementsFile) --quiet
    if ($LASTEXITCODE -eq 0) {
        $installed = $true
        Write-Host "  ✓ Dependencies installed from $RequirementsFile." -ForegroundColor Green
    }
}

if (-not $installed) {
    Write-Host "  ⚠ No pyproject.toml or $RequirementsFile found. Skipping dependency installation." -ForegroundColor DarkYellow
}

# 6. Verify critical packages (example for this project)
Write-Host "`n[6/7] Verifying key packages..." -ForegroundColor Yellow
$critical = @("pydantic", "charset-normalizer")
foreach ($pkg in $critical) {
    $check = python -c "import $pkg; print($pkg.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $pkg $check" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $pkg not importable" -ForegroundColor DarkYellow
    }
}

# 7. Git hygiene (agent must stay clean)
Write-Host "`n[7/7] Git status check..." -ForegroundColor Yellow
try {
    $branch = git rev-parse --abbrev-ref HEAD 2>&1
    Write-Host "  Current branch: $branch" -ForegroundColor Gray
    $status = git status --porcelain 2>&1
    if ($status) {
        Write-Host "  ⚠ Uncommitted changes present (agent should commit before major steps)." -ForegroundColor DarkYellow
    } else {
        Write-Host "  ✓ Working tree clean." -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ Git not available or not a repo." -ForegroundColor DarkYellow
}

Write-Host "`n=== Environment ready for agentic loop ===" -ForegroundColor Cyan
Write-Host "To reactivate in a new shell: . .\$VenvDir\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "Agent should call this script at the start of every major cycle." -ForegroundColor Gray
