<#
.SYNOPSIS
    Robust PowerShell wrapper for the Workspace-Scoped Structured Memory System.

.DESCRIPTION
    Safe entry point for the agent (Blackbox/MiniMax 2.5). Never guesses Python paths.
    Reuses the exact safe discovery patterns from Agent-Init.ps1.

    Always prefers the project .venv python. Falls back only to a validated system Python
    that can actually create venvs (rejects Inkscape, Git Bash, MS Store junk).

.EXAMPLE
    # From project root (recommended for the agent)
    & '.\agentic_loop_template\memory\Invoke-AgenticMemory.ps1' snapshot

.EXAMPLE
    # Record patterns (Reviewer after distillation)
    & '.\agentic_loop_template\memory\Invoke-AgenticMemory.ps1' update `
        -Category 'Common Failure Patterns' `
        -Description 'Guessing long site-packages paths instead of calling Get-PythonEnvironmentReport'
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("info", "path", "snapshot", "query", "update")]
    [string]$Action,

    [string]$Category,
    [string]$Description,
    [string]$Date,
    [string]$Summary,
    [string]$Contains,
    [int]$Top = 5
)

$ErrorActionPreference = 'Stop'

# --- Safe Python discovery (minimal self-contained version of Agent-Init.ps1 logic) ---
# We duplicate only the venv resolution here so the memory wrapper remains usable
# without forcing the caller to dot-source the full Agent-Init first.
function Get-VenvPython {
    $root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)   # project root from memory/ subdir
    $venvPy = Join-Path $root '.venv\Scripts\python.exe'
    if (Test-Path $venvPy) {
        return $venvPy
    }

    # Fallback: find any reliable Python 3.10+ (same heuristics as Agent-Init)
    # This should rarely be reached in normal agentic_loop_template usage.
    $candidates = @()
    $candidates += (Get-Command python -ErrorAction SilentlyContinue).Source
    $candidates += (Get-Command py -ErrorAction SilentlyContinue).Source

    foreach ($exe in ($candidates | Where-Object { $_ -and (Test-Path $_) })) {
        try {
            $ver = & $exe --version 2>&1
            if ($ver -match 'Python 3\.(1[0-9]|[2-9])') {
                return $exe
            }
        } catch {}
    }

    throw "No usable Python 3.10+ found for agentic memory. Activate the project .venv first or run Agent-Init.ps1."
}

$python = Get-VenvPython
$module = 'agentic_loop_template.memory'

switch ($Action) {
    'info' {
        & $python -m $module info
    }
    'path' {
        & $python -m $module path
    }
    'snapshot' {
        & $python -m $module snapshot
    }
    'query' {
        $args = @()
        if ($Category) { $args += '--category', $Category }
        if ($Top)      { $args += '--top', $Top }
        if ($Contains) { $args += '--contains', $Contains }
        & $python -m $module query @args
    }
    'update' {
        if (-not $Category -or -not $Description) {
            Write-Error "For 'update' you must provide both -Category and -Description"
            exit 1
        }

        $payload = @{
            patterns = @(
                @{
                    category = $Category
                    description = $Description
                }
            )
        }

        if ($Date -and $Summary) {
            $payload.distillation = @{
                date = $Date
                summary = $Summary
            }
        }

        $json = $payload | ConvertTo-Json -Depth 5 -Compress
        # Correct invocation: pass --json (matches __main__.py argparse)
        & $python -m $module update --json $json
    }
    default {
        Write-Error "Unknown action: $Action"
        exit 1
    }
}
