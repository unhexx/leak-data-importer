# setup_env.ps1 — Подготовка окружения для проекта
# Запуск: powershell -ExecutionPolicy Bypass -File .\scripts\setup_env.ps1

param(
    [string]$PythonVersion = "3.11",
    [string]$VenvDir = ".venv",
    [string]$RequirementsFile = "requirements.txt"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Подготовка окружения ===" -ForegroundColor Cyan

# ─── 1. Проверка Python ────────────────────────────────────────────────────────
Write-Host "`n[1/6] Проверка Python..." -ForegroundColor Yellow
$pythonExe = $null
foreach ($candidate in @("python", "python3", "py")) {
    try {
        $version = & $candidate --version 2>&1
        if ($version -match "Python $PythonVersion") {
            $pythonExe = $candidate
            Write-Host "  ✓ Найден: $version ($candidate)" -ForegroundColor Green
            break
        }
    } catch { }
}

if (-not $pythonExe) {
    Write-Error "Python $PythonVersion не найден. Установите Python $PythonVersion и добавьте в PATH."
    exit 1
}

# ─── 2. Создание виртуального окружения ───────────────────────────────────────
Write-Host "`n[2/6] Создание виртуального окружения в $VenvDir..." -ForegroundColor Yellow
if (Test-Path $VenvDir) {
    Write-Host "  ✓ Окружение уже существует, пропускаем создание." -ForegroundColor Green
} else {
    & $pythonExe -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Write-Error "Не удалось создать venv."; exit 1 }
    Write-Host "  ✓ Окружение создано." -ForegroundColor Green
}

# ─── 3. Активация окружения ───────────────────────────────────────────────────
Write-Host "`n[3/6] Активация окружения..." -ForegroundColor Yellow
$activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Error "Скрипт активации не найден: $activateScript"
    exit 1
}
. $activateScript
Write-Host "  ✓ Окружение активировано." -ForegroundColor Green

# ─── 4. Обновление pip (через venv python) ─────────────────────────────────────
Write-Host "`n[4/6] Обновление pip..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip --quiet 2>&1 | Out-Null
Write-Host "  ✓ pip обновлён." -ForegroundColor Green

# ─── 5. Установка зависимостей ────────────────────────────────────────────────
Write-Host "`n[5/6] Установка зависимостей из $RequirementsFile..." -ForegroundColor Yellow
if (Test-Path $RequirementsFile) {
    & $VenvPython -m pip install -r $RequirementsFile --quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Error "Ошибка установки зависимостей."; exit 1 }
    Write-Host "  ✓ Зависимости установлены." -ForegroundColor Green
} elseif (Test-Path "pyproject.toml") {
    & $VenvPython -m pip install -e ".[dev]" --quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Error "Ошибка установки через pyproject.toml."; exit 1 }
    Write-Host "  ✓ Установлено через pyproject.toml." -ForegroundColor Green
} else {
    Write-Host "  ⚠ Файл зависимостей не найден ($RequirementsFile / pyproject.toml). Пропускаем." -ForegroundColor DarkYellow
}

# ─── 6. Проверка git ──────────────────────────────────────────────────────────
Write-Host "`n[6/6] Проверка git..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    Write-Host "  ✓ $gitVersion" -ForegroundColor Green
    
    $currentBranch = git rev-parse --abbrev-ref HEAD 2>&1
    Write-Host "  ✓ Текущая ветка: $currentBranch" -ForegroundColor Green
    
    $gitStatus = git status --short 2>&1
    if ($gitStatus) {
        Write-Host "  ⚠ Незакоммиченные изменения:" -ForegroundColor DarkYellow
        $gitStatus | ForEach-Object { Write-Host "    $_" }
    } else {
        Write-Host "  ✓ Рабочая директория чистая." -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ git не найден или не инициализирован." -ForegroundColor DarkYellow
}

# ─── Итог ─────────────────────────────────────────────────────────────────────
Write-Host "`n=== Окружение готово к работе ===" -ForegroundColor Cyan
Write-Host "Для активации окружения в новой сессии: . .\$VenvDir\Scripts\Activate.ps1" -ForegroundColor Gray
