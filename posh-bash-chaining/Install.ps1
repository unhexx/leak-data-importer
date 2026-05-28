<#
.SYNOPSIS
    Установка posh-bash-chaining в профиль текущего пользователя.

.DESCRIPTION
    Безопасно добавляет загрузку Enable-BashChaining.ps1 в PowerShell-профиль.
    Если строка уже есть — ничего не делает.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$mainScript = Join-Path $scriptDir 'Enable-BashChaining.ps1'

if (-not (Test-Path $mainScript)) {
    Write-Error "Не найден Enable-BashChaining.ps1 рядом с Install.ps1"
    exit 1
}

$profilePath = $PROFILE.CurrentUserAllHosts

# Создаём профиль, если его ещё нет
if (-not (Test-Path $profilePath)) {
    $profileDir = Split-Path $profilePath -Parent
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    New-Item -Path $profilePath -ItemType File -Force | Out-Null
    Write-Host "Создан новый профиль: $profilePath" -ForegroundColor Yellow
}

# Формируем строку подключения
$loadLine = ". '$mainScript'"

# Проверяем, не подключён ли уже инструмент
$currentProfile = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($currentProfile -and $currentProfile.Contains($loadLine)) {
    Write-Host "posh-bash-chaining уже подключён в профиле." -ForegroundColor Green
    return
}

# Добавляем в конец профиля
Add-Content -Path $profilePath -Value "`n# posh-bash-chaining (bash-операторы в PowerShell 5.1)`n$loadLine`n"

Write-Host ""
Write-Host "✓ posh-bash-chaining успешно добавлен в профиль." -ForegroundColor Green
Write-Host ""
Write-Host "Чтобы изменения вступили в силу, выполни один из вариантов:" -ForegroundColor DarkGray
Write-Host "  1. Перезапусти PowerShell" -ForegroundColor DarkGray
Write-Host "  2. . `$PROFILE" -ForegroundColor DarkGray
Write-Host ""
Write-Host "После этого можно будет писать команды с &&, ||, |& и &>." -ForegroundColor DarkGray
Write-Host ""
Write-Host "Проверить статус: Get-BashChainingStatus" -ForegroundColor DarkGray
Write-Host ""