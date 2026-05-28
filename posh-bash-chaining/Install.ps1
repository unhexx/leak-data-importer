<# 
.SYNOPSIS
    Установка posh-bash-chaining с поддержкой неинтерактивных сессий.

.DESCRIPTION
    Этот скрипт делает так, чтобы Enable-BashChaining.ps1 загружался
    даже когда агенты (Blackbox, Continue и др.) запускают новые процессы PowerShell
    без интерактивного терминала.

    Для этого он добавляет лёгкий bootstrap в самое начало твоего $PROFILE.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bootstrapScript = Join-Path $scriptDir 'Profile-Bootstrap.ps1'

if (-not (Test-Path $bootstrapScript)) {
    Write-Error "Не найден Profile-Bootstrap.ps1"
    exit 1
}

$profilePath = $PROFILE.CurrentUserAllHosts

# Создаём профиль, если его нет
if (-not (Test-Path $profilePath)) {
    $dir = Split-Path $profilePath -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    New-Item -Path $profilePath -ItemType File -Force | Out-Null
    Write-Host "Создан новый файл профиля: $profilePath" -ForegroundColor Yellow
}

# === 1. Чистим все старые упоминания posh-bash-chaining ===
$raw = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($null -eq $raw) { $raw = '' }
if ($raw -is [array]) { $raw = $raw -join "`r`n" }

$patternsToRemove = @(
    'posh-bash-chaining',
    'Profile-Bootstrap\.ps1',
    'Enable-BashChaining\.ps1',
    'scripts\\Enable-BashChaining'
)

$cleaned = $raw
foreach ($pattern in $patternsToRemove) {
    $cleaned = $cleaned -replace "(?m)^.*$pattern.*\r?\n?", ""
}

if ($cleaned -ne $raw) {
    Set-Content -Path $profilePath -Value $cleaned.TrimEnd() -Encoding UTF8
    Write-Host "Удалены старые ссылки posh-bash-chaining из профиля." -ForegroundColor Yellow
    $raw = $cleaned
}

# === 2. Формируем строку для вставки в самое начало профиля ===
$bootstrapLine = ". '$bootstrapScript'"

# Проверяем, не стоит ли уже актуальная версия
if ($raw -and $raw.Contains($bootstrapLine)) {
    Write-Host "posh-bash-chaining уже настроен для загрузки в профиле." -ForegroundColor Green
    return
}

# === 3. Вставляем bootstrap в самое начало профиля ===
# Это критично для неинтерактивных сессий
$newContent = $bootstrapLine + "`r`n" + $raw

Set-Content -Path $profilePath -Value $newContent.TrimEnd() -Encoding UTF8

Write-Host ""
Write-Host "✓ posh-bash-chaining настроен для работы в обычных и неинтерактивных сессиях." -ForegroundColor Green
Write-Host ""
Write-Host "В начало твоего профиля добавлена строка:" -ForegroundColor DarkGray
Write-Host "    $bootstrapLine" -ForegroundColor White
Write-Host ""
Write-Host "Теперь инструмент будет подключаться автоматически," -ForegroundColor DarkGray
Write-Host "даже если агент запускает новые процессы PowerShell." -ForegroundColor DarkGray
Write-Host ""
Write-Host "Рекомендация: полностью перезапусти терминал в VSCode." -ForegroundColor Yellow
Write-Host ""