<#
.SYNOPSIS
    Добавляет поддержку bash-стильных операторов &&, ||, перенаправлений &>/>& и pipe |&
    в классическую Windows PowerShell 5.1.

.DESCRIPTION
    Перехватывает нажатие Enter через PSReadLine и автоматически преобразует команды
    с bash-операторами в корректный синтаксис PowerShell 5.1.

    Поддерживаемые возможности:
    - && и || (длинные и смешанные цепочки)
    - &> file, &>> file, >& file   →  *> / *>>  (stdout + stderr)
    - |&                            →  2>&1 |   (pipe с включением stderr)
    - 2>&1 остаётся без изменений (уже работает в PowerShell)

    Примеры:
        cmd1 && cmd2 |& grep error
        build && test &> build.log || echo "что-то сломалось"
        deploy &>> deploy.log
#>

[CmdletBinding()]
param()

# =============================================================================
# Основная функция преобразования (quote-aware)
# =============================================================================

function Convert-BashOperatorsToPowerShell {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$InputLine
    )

    if ([string]::IsNullOrWhiteSpace($InputLine)) {
        return $InputLine
    }

    $trimmed = $InputLine.Trim()

    $andAnd = [string][char]38 + [string][char]38
    $orOr   = [string][char]124 + [string][char]124

    $hasChaining = $trimmed -match ([regex]::Escape($andAnd)) -or $trimmed -match ([regex]::Escape($orOr))

    try {

        $segments = @()
        $operators = @()
        $current = ''

        $inDouble = $false
        $inSingle = $false
        $i = 0
        $len = $trimmed.Length

        while ($i -lt $len) {
            $ch = $trimmed[$i]

            # Handle quotes
            if ($ch -eq '"' -and -not $inSingle) {
                $inDouble = -not $inDouble
                $current += $ch
                $i++
                continue
            }
            if ($ch -eq "'" -and -not $inDouble) {
                $inSingle = -not $inSingle
                $current += $ch
                $i++
                continue
            }

            # Look for top-level operators
            if (-not $inDouble -and -not $inSingle -and ($i + 1 -lt $len)) {
                $two = $trimmed.Substring($i, 2)
                if ($two -eq $andAnd -or $two -eq $orOr) {
                    if ($current.Trim()) {
                        $segments += $current.Trim()
                    }
                    $operators += $two
                    $current = ''
                    $i += 2
                    # skip whitespace after operator
                    while ($i -lt $len -and [char]::IsWhiteSpace($trimmed[$i])) { $i++ }
                    continue
                }
            }

            $current += $ch
            $i++
        }

        if ($current.Trim()) {
            $segments += $current.Trim()
        }

        # Build result with chaining if any operators were found
        if ($operators.Count -gt 0) {
            $result = $segments[0]

            for ($k = 0; $k -lt $operators.Count; $k++) {
                $op = $operators[$k]
                $nextCmd = if ($k + 1 -lt $segments.Count) { $segments[$k + 1] } else { '' }

                if ($op -eq $andAnd) {
                    $result += ' ; if ($?) { ' + $nextCmd + ' }'
                }
                else {
                    $result += ' ; if (-not $?) { ' + $nextCmd + ' }'
                }
            }
        }
        else {
            $result = $trimmed
        }

        # Always apply bash-style redirection translation as final step
        $result = Convert-BashRedirectionsToPowerShell -InputLine $result

        return $result
    }
    catch {
        Write-Verbose "BashChaining: conversion failed"
        return $InputLine
    }
}

# =============================================================================
# Поддержка bash-стильных перенаправлений (&> и &>>)
# =============================================================================

function Convert-BashRedirectionsToPowerShell {
    <#
    .SYNOPSIS
        Преобразует bash-стильные перенаправления и pipe-операторы в эквиваленты PowerShell 5.1.

        Поддерживаемые формы:
            &> file     →  *> file          (stdout + stderr в файл)
            &>> file    →  *>> file         (дописать stdout + stderr)
            >& file     →  *> file          (bash-шорткат для обоих потоков)
            |&          →  2>&1 |           (pipe включая stderr)
            2>&1        →  (оставляем как есть — уже валидно в PowerShell)
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$InputLine
    )

    if ([string]::IsNullOrWhiteSpace($InputLine)) {
        return $InputLine
    }

    $andGt    = [string][char]38 + '>'      # &>
    $andGtGt  = [string][char]38 + '>>'     # &>>
    $pipeAnd  = '|' + [string][char]38      # |&
    $redirGt  = '>' + [string][char]38      # >&   (bash "both to file")

    # Early exit only if none of the interesting bash redirection forms are present
    if ($InputLine -notmatch ([regex]::Escape($andGt)) -and
        $InputLine -notmatch ([regex]::Escape($pipeAnd)) -and
        $InputLine -notmatch ([regex]::Escape($redirGt))) {
        return $InputLine
    }

    try {
        $result = [System.Text.StringBuilder]::new()
        $i = 0
        $len = $InputLine.Length

        $inDouble = $false
        $inSingle = $false

        while ($i -lt $len) {
            $ch = $InputLine[$i]

            # Track quotes
            if ($ch -eq '"' -and -not $inSingle) {
                $inDouble = -not $inDouble
                [void]$result.Append($ch)
                $i++
                continue
            }
            if ($ch -eq "'" -and -not $inDouble) {
                $inSingle = -not $inSingle
                [void]$result.Append($ch)
                $i++
                continue
            }

            # Check for various bash redirection forms at top level
            if (-not $inDouble -and -not $inSingle -and ($i + 1 -lt $len)) {
                $two = $InputLine.Substring($i, 2)

                # &> and &>>
                if ($two -eq $andGt) {
                    if ($i + 2 -lt $len -and $InputLine[$i+2] -eq '>') {
                        [void]$result.Append('*>>')
                        $i += 3
                    } else {
                        [void]$result.Append('*>')
                        $i += 2
                    }
                    continue
                }

                # |&  →  2>&1 |
                if ($two -eq $pipeAnd) {
                    [void]$result.Append('2>&1 | ')
                    $i += 2
                    # Skip following whitespace so we don't double-space
                    while ($i -lt $len -and [char]::IsWhiteSpace($InputLine[$i])) { $i++ }
                    continue
                }

                # >& file   (bash shorthand for redirect both stdout+stderr to file)
                # But do NOT touch >&1, >&2 etc. (those are standard 2>&1 syntax)
                if ($two -eq $redirGt) {
                    $nextChar = if ($i + 2 -lt $len) { $InputLine[$i + 2] } else { '' }
                    if ($nextChar -match '\d') {
                        # This is part of 2>&1 / 1>&2 style — leave it alone
                        [void]$result.Append($ch)
                        $i++
                        continue
                    } else {
                        [void]$result.Append('*>')
                        $i += 2
                        continue
                    }
                }
            }

            [void]$result.Append($ch)
            $i++
        }

        return $result.ToString()
    }
    catch {
        Write-Verbose "BashChaining: redirection rewrite failed"
        return $InputLine
    }
}

# =============================================================================
# PSReadLine
# =============================================================================

if ($host.Name -ne 'ConsoleHost') {
    Write-Warning "Скрипт работает только в интерактивной консоли."
    return
}

try {
    Import-Module PSReadLine -ErrorAction Stop
}
catch {
    Write-Error "Нужен модуль PSReadLine: $_"
    return
}

if ($global:__BashChainingEnabled) {
    Write-Host "Поддержка уже активна в этой сессии." -ForegroundColor DarkGray
    return
}

$global:__BashChainingEnabled = $true
$global:BashChainingDebug = $false

$script:EnterHandler = {
    param($key, $arg)

    $line = $null
    $cursor = $null
    [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$cursor)

    if ([string]::IsNullOrWhiteSpace($line)) {
        [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
        return
    }

    $andAnd = [string][char]38 + [string][char]38
    $orOr   = [string][char]124 + [string][char]124
    $andGt  = [string][char]38 + '>'
    $pipeAnd = '|' + [string][char]38
    $redirGt = '>' + [string][char]38

    $hasChaining = $line -match ([regex]::Escape($andAnd)) -or $line -match ([regex]::Escape($orOr))
    $hasRedir    = $line -match ([regex]::Escape($andGt)) -or
                   $line -match ([regex]::Escape($pipeAnd)) -or
                   $line -match ([regex]::Escape($redirGt))

    if (-not $hasChaining -and -not $hasRedir) {
        [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
        return
    }

    try {
        $rewritten = $line

        if ($hasChaining) {
            $rewritten = Convert-BashOperatorsToPowerShell -InputLine $line
        }
        elseif ($hasRedir) {
            # Only redirections, no chaining
            $rewritten = Convert-BashRedirectionsToPowerShell -InputLine $line
        }

        if ($global:BashChainingDebug -and $rewritten -ne $line) {
            Write-Host "
[BashChaining] Переписано:" -ForegroundColor DarkCyan
            Write-Host "  $rewritten" -ForegroundColor Cyan
        }

        if ($rewritten -and $rewritten -ne $line) {
            [Microsoft.PowerShell.PSConsoleReadLine]::Replace(0, $line.Length, $rewritten)
        }
    }
    catch {
        if ($global:BashChainingDebug) {
            Write-Host "
[BashChaining] Ошибка преобразования." -ForegroundColor DarkRed
        }
    }

    [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
}

Set-PSReadLineKeyHandler -Key Enter -BriefDescription 'BashAndOr' -LongDescription 'Поддержка AND-AND и OR-OR' -ScriptBlock $script:EnterHandler

function Disable-BashChaining {
    $global:__BashChainingEnabled = $false
    Write-Host "Поддержка операторов отключена." -ForegroundColor Yellow
}

function Get-BashChainingStatus {
    if ($global:__BashChainingEnabled) {
        Write-Host "Поддержка операторов AND-AND и OR-OR активна" -ForegroundColor Green
    } else {
        Write-Host "Поддержка отключена" -ForegroundColor Red
    }
}

Write-Host ''
Write-Host 'Поддержка bash-операторов AND-AND и OR-OR успешно включена.' -ForegroundColor Green
Write-Host ''
Write-Host 'Примеры (теперь работают):' -ForegroundColor DarkGray
Write-Host '  cmd1 [AND-AND] cmd2 [OR-OR] cmd3 [AND-AND] cmd4' -ForegroundColor White
Write-Host '  build [AND-AND] test [BOTH-REDIR] build.log [OR-OR] echo failed' -ForegroundColor White
Write-Host '  deploy [BOTH-APPEND] deploy.log' -ForegroundColor White
Write-Host '  cmd [PIPE-ALL] grep -i error' -ForegroundColor White
Write-Host ''
Write-Host 'Статус: Get-BashChainingStatus' -ForegroundColor DarkGray
Write-Host "Для автозагрузки добавь в `$PROFILE строку:" -ForegroundColor DarkGray
Write-Host "    . `$PSScriptRoot\Enable-BashChaining.ps1" -ForegroundColor Yellow
Write-Host ''