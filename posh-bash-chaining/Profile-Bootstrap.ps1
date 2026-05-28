<#
.SYNOPSIS
    Лёгкий загрузчик posh-bash-chaining для профиля PowerShell.

.DESCRIPTION
    Этот файл предназначен для автоматического подключения из $PROFILE.
    Он позволяет инструменту работать даже в неинтерактивных сессиях
    (когда агенты в VSCode запускают новые процессы PowerShell с -Command или -File).

    В неинтерактивном режиме загружается только логика преобразования команд
    (без PSReadLine), чтобы не ломать захват вывода у агента.

    Устанавливается автоматически через Install.ps1.
#>

[CmdletBinding()]
param()

# Save original preference and restore it after loading.
# IMPORTANT: We no longer leave $ErrorActionPreference set to SilentlyContinue
# globally (this was causing missing output in many commands).
# We only use it temporarily while loading the main script.
$__originalErrorAction = $ErrorActionPreference

try {
    $ErrorActionPreference = 'SilentlyContinue'

    # Определяем путь к основному скрипту относительно этого файла
    $__poshBashChainingMain = Join-Path $PSScriptRoot 'Enable-BashChaining.ps1'

    if (Test-Path $__poshBashChainingMain) {
        . $__poshBashChainingMain
    }
}
finally {
    # Always restore the original preference
    $ErrorActionPreference = $__originalErrorAction
}
