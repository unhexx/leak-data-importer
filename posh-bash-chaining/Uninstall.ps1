<#
.SYNOPSIS
    Удаление posh-bash-chaining из профиля PowerShell.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$mainScript = Join-Path $scriptDir 'Enable-BashChaining.ps1'
$loadLine = ". '$mainScript'"

$profilePath = $PROFILE.CurrentUserAllHosts

if (-not (Test-Path $profilePath)) {
    Write-Host "Профиль не существует — нечего удалять." -ForegroundColor Yellow
    return
}

$content = Get-Content $profilePath -Raw

if ($content -notlike "*$loadLine*") {
    Write-Host "posh-bash-chaining не найден в профиле." -ForegroundColor Yellow
    return
}

$newContent = ($content -split "`r?`n" | Where-Object { $_ -notlike "*$loadLine*" }) -join "`r`n"
Set-Content -Path $profilePath -Value $newContent.TrimEnd()

Write-Host "✓ posh-bash-chaining удалён из профиля." -ForegroundColor Green
Write-Host "Перезапусти PowerShell, чтобы изменения применились." -ForegroundColor DarkGray
