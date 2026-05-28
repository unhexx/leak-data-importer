<#
.SYNOPSIS
    Установка / обновление posh-bash-chaining в профиль текущего пользователя.

.DESCRIPTION
    - Удаляет старые ссылки на Enable-BashChaining.ps1 (в т.ч. из старой папки scripts/)
    - Добавляет актуальную версию из posh-bash-chaining/
    - Безопасно работает при повторных запусках
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

# === Очистка старых ссылок (очень важно!) ===
$oldPatterns = @(
    'scripts\\Enable-BashChaining\.ps1',
    'Enable-BashChaining\.ps1'
)

$content = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
$originalContent = $content

foreach ($pattern in $oldPatterns) {
    # Удаляем строки, которые содержат старые пути
    $content = $content -replace "(?m)^.*$pattern.*\r?\n?", ""
}

if ($content -ne $originalContent) {
    Set-Content -Path $profilePath -Value $content.TrimEnd() -Encoding UTF8
    Write-Host "Удалены старые ссылки на Enable-BashChaining.ps1 из профиля." -ForegroundColor Yellow
}

# Формируем актуальную строку подключения
$loadLine = ". '$mainScript'"

# Проверяем, не подключён ли уже актуальный вариант
$currentProfile = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($currentProfile -and $currentProfile.Contains($loadLine)) {
    Write-Host "posh-bash-chaining уже подключён в профиле (актуальная версия)." -ForegroundColor Green
    return
}

# Добавляем в конец профиля
Add-Content -Path $profilePath -Value "`n# posh-bash-chaining (bash-операторы в PowerShell 5.1)`n$loadLine`n" -Encoding UTF8

Write-Host ""
Write-Host "✓ posh-bash-chaining успешно установлен / обновлён в профиле." -ForegroundColor Green
Write-Host ""
Write-Host "Чтобы изменения вступили в силу:" -ForegroundColor DarkGray
Write-Host "  1. Перезапусти терминал в VSCode" -ForegroundColor DarkGray
Write-Host "  2. Или выполни:  . `$PROFILE" -ForegroundColor DarkGray
Write-Host ""
Write-Host "После этого команды с &&, ||, |& и &> начнут работать." -ForegroundColor DarkGray
Write-Host ""
Write-Host "Проверить статус: Get-BashChainingStatus" -ForegroundColor DarkGray
Write-Host ""