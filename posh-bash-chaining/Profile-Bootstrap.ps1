<#
.SYNOPSIS
    Лёгкий загрузчик posh-bash-chaining для профиля PowerShell.

.DESCRIPTION
    Этот файл предназначен для автоматического подключения из $PROFILE.
    Он позволяет инструменту работать даже в неинтерактивных сессиях
    (когда агенты в VSCode запускают новые процессы PowerShell с -Command или -File).

    Устанавливается автоматически через Install.ps1.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'SilentlyContinue'

# Определяем путь к основному скрипту относительно этого файла
$__poshBashChainingMain = Join-Path $PSScriptRoot 'Enable-BashChaining.ps1'

if (Test-Path $__poshBashChainingMain) {
    . $__poshBashChainingMain
}
