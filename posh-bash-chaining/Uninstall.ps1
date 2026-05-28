<#
.SYNOPSIS
    Удаление posh-bash-chaining из профиля PowerShell.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bootstrapScript = Join-Path $scriptDir 'Profile-Bootstrap.ps1'
$bootstrapLine = ". '$bootstrapScript'"

$profilePath = $PROFILE.CurrentUserAllHosts

if (-not (Test-Path $profilePath)) {
    Write-Host "Профиль не существует — нечего удалять." -ForegroundColor Yellow
    return
}

$content = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($null -eq $content) { $content = '' }
if ($content -is [array]) { $content = $content -join "`r`n" }

$hasBootstrap = $content -like "*$bootstrapLine*"

# Также чистим старые прямые ссылки на Enable-BashChaining
$oldPatterns = @('Enable-BashChaining\.ps1', 'scripts\\Enable-BashChaining')

$cleaned = $content
foreach ($pat in $oldPatterns) {
    $cleaned = $cleaned -replace "(?m)^.*$pat.*\r?\n?", ""
}

if (-not $hasBootstrap -and ($cleaned -eq $content)) {
    Write-Host "posh-bash-chaining не найден в профиле." -ForegroundColor Yellow
    return
}

# Удаляем строку с bootstrap
$newContent = ($cleaned -split "`r?`n" | Where-Object { $_ -notlike "*$bootstrapLine*" }) -join "`r`n"

Set-Content -Path $profilePath -Value $newContent.TrimEnd() -Encoding UTF8

Write-Host "✓ posh-bash-chaining полностью удалён из профиля." -ForegroundColor Green
Write-Host "Перезапусти PowerShell, чтобы изменения применились." -ForegroundColor DarkGray
