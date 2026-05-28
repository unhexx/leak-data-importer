<#
.SYNOPSIS
    Initialization script for Blackbox + MiniMax2.5 in VSCode.
    Prepares Python venv and can generate a ready-to-use agent starter prompt.
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

function Get-AutoTaskDescription {
    param([int]$MaxLength = 2800)

    $candidates = @(
        (Join-Path $ProjectRoot "TASK_SPECIFICATION.md"),
        (Join-Path $ProjectRoot "TODO.md")
    )

    foreach ($file in $candidates) {
        if (Test-Path $file) {
            try {
                $raw = Get-Content $file -Raw -ErrorAction Stop
                if ($raw.Length -gt $MaxLength) {
                    $raw = $raw.Substring(0, $MaxLength) + "`n... (truncated)"
                }
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
        "1. Run this first:",
        "   powershell -ExecutionPolicy Bypass -File .\agentic_loop_template\Agent-Init.ps1",
        "",
        "2. Activate venv:",
        "   . .\.venv\Scripts\Activate.ps1",
        "",
        "3. Read in order:",
        "   - docs/agentic_loop/README.md",
        "   - docs/agentic_loop/SYSTEM_PROMPT.md",
        "   - docs/agentic_loop/Agent-Init.md",
        "   - $SpecFile",
        "",
        "4. Start as ORCHESTRATOR.",
        "",
        "Rules: Use natural Russian developer-style commit messages only. No AI/agent mentions in commits.",
        "Always work inside the local .venv."
    )

    return ($lines -join "`r`n")
}

# === Main Logic ===

# Environment setup (always run)
Write-Host "=== Agentic Environment Init ===" -ForegroundColor Cyan

# Locate Python (simplified)
$python = $null
foreach ($c in @("python","py")) { 
    try { if ((& $c --version 2>&1) -match "Python 3") { $python = $c; break } } catch {} 
}
if (-not $python) { Write-Error "Python not found"; exit 1 }

$venv = Join-Path $ProjectRoot ".venv"
$act  = Join-Path $venv "Scripts\Activate.ps1"

if (-not (Test-Path $venv)) { & $python -m venv $venv }
. $act

if (Test-Path (Join-Path $ProjectRoot "pyproject.toml")) {
    python -m pip install -e "$ProjectRoot.[dev]" --quiet
}

# Set safe flags for agents
$env:POSH_BASH_CHAINING_NONINTERACTIVE = "1"

Write-Host "Environment ready." -ForegroundColor Green

# Prompt generation
$task = $TaskDescription
if (-not $task) { $task = Get-AutoTaskDescription -MaxLength $MaxTaskLength }

if ($task) {
    $prompt = Generate-AgentStarterPrompt -Task $task -SpecFile $TaskSpecFile

    if ($OutputFile) {
        $out = if ([System.IO.Path]::IsPathRooted($OutputFile)) { $OutputFile } else { Join-Path $ProjectRoot $OutputFile }
        Set-Content -Path $out -Value $prompt -Encoding UTF8
        Write-Host "Prompt saved to $out" -ForegroundColor Green
    }

    Write-Host "`n=== Ready-to-use prompt for Blackbox ===`n" -ForegroundColor Yellow
    Write-Host $prompt
} else {
    Write-Host "No task description found. Provide one with -TaskDescription or create TODO.md / TASK_SPECIFICATION.md"
}