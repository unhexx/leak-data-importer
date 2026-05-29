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

    # Дополнительно: принудительно включаем UTF-8 defaults для чтения и записи файлов.
    # Это важно для неинтерактивных агентских сессий (Blackbox и т.п.),
    # чтобы handoff JSON и другие текстовые файлы не превращались в кракозябры на русских Windows.
    $PSDefaultParameterValues['Out-File:Encoding']       = 'utf8'
    $PSDefaultParameterValues['Set-Content:Encoding']    = 'utf8'
    $PSDefaultParameterValues['Add-Content:Encoding']    = 'utf8'
    $PSDefaultParameterValues['Get-Content:Encoding']    = 'utf8'
    $env:PYTHONIOENCODING = 'utf-8'

    # Попытка установить кодировку консоли (может не сработать в полностью неинтерактивных сессиях)
    try {
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        $OutputEncoding = [System.Text.Encoding]::UTF8
    } catch {}
}
finally {
    # Always restore the original preference
    $ErrorActionPreference = $__originalErrorAction
}
