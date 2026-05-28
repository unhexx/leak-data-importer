<#
.SYNOPSIS
    One-time / per-session initialization script for working with Blackbox AI + MiniMax2.5 in VSCode.

.DESCRIPTION
    This script prepares the local development environment so that an AI agent
    (especially Blackbox) can reliably work with the agentic_loop_template.

    It:
    - Creates and activates the Python virtual environment
    - Installs dependencies from pyproject.toml
    - Installs the posh-bash-chaining tool with agent-friendly settings
    - Sets environment variables that help non-interactive agents
    - Can automatically generate a high-quality starter prompt by reading
      TASK_SPECIFICATION.md or TODO.md (no need to pass -TaskDescription)
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
$TemplateDir = $PSScriptRoot

function Get-AutoTaskDescription {
    param([int]$MaxLength = 2800)

    $candidates = @(
        (Join-Path $ProjectRoot "TASK_SPECIFICATION.md"),
        (Join-Path $ProjectRoot "TODO.md"),
        (Join-Path $ProjectRoot "docs\TASK_SPECIFICATION.md")
    )

    foreach ($file in $candidates) {
        if (Test-Path $file) {
            try {
                $content = Get-Content $file -Raw -ErrorAction Stop
                $content = $content.Trim()

                if ($content.Length -gt $MaxLength) {
                    $content = $content.Substring(0, $MaxLength) + "`n... (truncated)"
                }

                Write-Host "  ✓ Auto-detected task from: $(Split-Path $file -Leaf)" -ForegroundColor Green
                return $content
            } catch {
                Write-Host "  ⚠ Could not read $file" -ForegroundColor DarkYellow
            }
        }
    }

    return $null
}

Write-Host "=== Agentic Loop Initialization for Blackbox + MiniMax2.5 ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot" -ForegroundColor Gray

# 1. Python Environment
Write-Host "`n[1/5] Preparing Python virtual environment..." -ForegroundColor Yellow

$python = $null
foreach ($cmd in @("python", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(1[0-9])") {
            $python = $cmd
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Error "Python 3.10+ not found. Please install Python and add it to PATH."
    exit 1
}

$venvPath = Join-Path $ProjectRoot ".venv"
$activate = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating .venv..." -ForegroundColor DarkYellow
    & $python -m venv $venvPath
}

. $activate
Write-Host "✓ Virtual environment activated." -ForegroundColor Green

# 2. Install dependencies
Write-Host "`n[2/5] Installing project dependencies..." -ForegroundColor Yellow
if (Test-Path (Join-Path $ProjectRoot "pyproject.toml")) {
    python -m pip install --upgrade pip --quiet
    python -m pip install -e "$ProjectRoot.[dev]" --quiet
    Write-Host "✓ Dependencies installed from pyproject.toml" -ForegroundColor Green
} else {
    Write-Host "⚠ No pyproject.toml found. Skipping dependency installation." -ForegroundColor DarkYellow
}

# 3. Install posh-bash-chaining (for && || |& support in agents)
Write-Host "`n[3/5] Setting up posh-bash-chaining (for bash-style operators)..." -ForegroundColor Yellow
$chainingDir = Join-Path $ProjectRoot "posh-bash-chaining"
if (Test-Path (Join-Path $chainingDir "Install.ps1")) {
    Push-Location $chainingDir
    .\Install.ps1 | Out-Null
    Pop-Location
    Write-Host "✓ posh-bash-chaining installed / updated." -ForegroundColor Green
} else {
    Write-Host "⚠ posh-bash-chaining not found in project." -ForegroundColor DarkYellow
}

# 4. Set environment variables helpful for Blackbox / non-interactive agents
Write-Host "`n[4/5] Setting agent-friendly environment variables..." -ForegroundColor Yellow

[Environment]::SetEnvironmentVariable("POSH_BASH_CHAINING_NONINTERACTIVE", "1", "User")
[Environment]::SetEnvironmentVariable("BLACKBOX_AGENT_MODE", "1", "User")

$env:POSH_BASH_CHAINING_NONINTERACTIVE = "1"
$env:BLACKBOX_AGENT_MODE = "1"

Write-Host "✓ Environment variables set for current session and user." -ForegroundColor Green

# 5. Generate task-specific starter prompt (if requested or auto-detected)
function Generate-AgentStarterPrompt {
    param(
        [string]$Task,
        [string]$SpecFile = "TASK_SPECIFICATION.md"
    )

    $prompt = @"
We are starting an autonomous agentic development loop using the template in `agentic_loop_template/`.

**Current Task:**
$Task

**Instructions for you (the agent):**

1. First, ensure the local Python environment is ready by running:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\agentic_loop_template\Agent-Init.ps1
   ```

2. Activate the virtual environment:
   ```powershell
   . .\.venv\Scripts\Activate.ps1
   ```

3. Read the following files in this exact order:
   - `docs/agentic_loop/README.md`
   - `docs/agentic_loop/SYSTEM_PROMPT.md`
   - `docs/agentic_loop/Agent-Init.md`
   - `$SpecFile` (this is the single source of truth for the task)

4. Begin working as **ORCHESTRATOR** according to the structure in `SYSTEM_PROMPT.md`.

**Strict Rules:**
- All git commit messages must be written in natural Russian, as a real human mid/senior developer who has been working on this project for a long time.
- Never mention AI, LLM, agent, MiniMax, Grok, Claude, or any other model name in commit messages.
- Always use the local `.venv` for Python commands.
- Work iteratively with small, well-tested changes.
- Follow the full Orchestrator → Coder → Tester → Debugger → Reviewer cycle.

Start now by assessing the current state of the repository and the task specification.
"@

    return $prompt
}

# === Auto-detect task description if not provided ===
$finalTaskDescription = $TaskDescription
$finalSpecFile = $TaskSpecFile

if (-not $finalTaskDescription) {
    Write-Host "`n[5/5] No explicit task description provided. Trying to auto-detect..." -ForegroundColor Yellow
    $autoTask = Get-AutoTaskDescription -MaxLength $MaxTaskLength

    if ($autoTask) {
        $finalTaskDescription = $autoTask
        Write-Host "  Using auto-detected task description." -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Could not auto-detect task from TASK_SPECIFICATION.md or TODO.md" -ForegroundColor DarkYellow
        Write-Host "    You can provide it manually with -TaskDescription" -ForegroundColor DarkYellow
    }
}

# Main prompt generation logic
if ($GeneratePromptOnly -or $finalTaskDescription) {
    Write-Host "`nGenerating task-specific starter prompt for the agent..." -ForegroundColor Cyan

    $generatedPrompt = Generate-AgentStarterPrompt -Task $finalTaskDescription -SpecFile $finalSpecFile

    if ($OutputFile) {
        $fullOutputPath = if ([System.IO.Path]::IsPathRooted($OutputFile)) { $OutputFile } else { Join-Path $ProjectRoot $OutputFile }
        Set-Content -Path $fullOutputPath -Value $generatedPrompt -Encoding UTF8
        Write-Host "✓ Prompt saved to: $fullOutputPath" -ForegroundColor Green
    }

    Write-Host "`n=== Generated Starter Prompt for Blackbox ===" -ForegroundColor Yellow
    Write-Host $generatedPrompt -ForegroundColor Gray
    Write-Host "=============================================" -ForegroundColor Yellow

    if (-not $GeneratePromptOnly) {
        Write-Host "`nEnvironment is prepared. You can copy the prompt above and send it to the agent." -ForegroundColor Green
    }

    exit 0
}

# Normal (non-prompt-only) final instructions
Write-Host "`n[5/5] Initialization complete." -ForegroundColor Cyan

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Completely restart the terminal in VSCode (important)." -ForegroundColor White
Write-Host ""
Write-Host "2. Copy and paste the following as the FIRST message to Blackbox:" -ForegroundColor White
Write-Host ""
Write-Host "────────────────────────────────────────────────────────────" -ForegroundColor DarkGray

@"
We are using the Agentic Loop Template.

Please read these files in order:
- docs/agentic_loop/README.md
- docs/agentic_loop/SYSTEM_PROMPT.md
- docs/agentic_loop/Agent-Init.md

Then run this command to prepare the environment:
powershell -ExecutionPolicy Bypass -File .\agentic_loop_template\Agent-Init.ps1

After that, activate the venv and begin working as ORCHESTRATOR according to the SYSTEM_PROMPT.

Remember: all commit messages must be in natural Russian, written as a real human developer (no mention of AI or agents).
"@ | Write-Host -ForegroundColor Gray

Write-Host "────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
Write-Host "You can now start giving tasks to the Blackbox agent." -ForegroundColor Green
Write-Host ""
Write-Host "Tip: If the agent gets confused about the environment later, just tell it:" -ForegroundColor DarkGray
Write-Host "     'Run: powershell -ExecutionPolicy Bypass -File .\agentic_loop_template\Agent-Init.ps1'" -ForegroundColor DarkGray
Write-Host ""
Write-Host "To generate a task-specific starter prompt automatically, run:" -ForegroundColor DarkGray
Write-Host "     .\agentic_loop_template\Agent-Init.ps1 -TaskDescription 'Your task here' -TaskSpecFile 'TASK_SPECIFICATION.md' -OutputFile 'start_prompt.txt'" -ForegroundColor DarkGray
Write-Host ""
