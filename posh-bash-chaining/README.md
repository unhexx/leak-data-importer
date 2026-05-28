# posh-bash-chaining

Поддержка bash-операторов в классической Windows PowerShell 5.1

Позволяет использовать привычные конструкции `&&`, `||`, `|&`, `&>` и `>&` прямо в PowerShell, как в bash или cmd.

## Зачем это нужно

В Windows PowerShell 5.1 (той, что идёт по умолчанию) нельзя писать:

```powershell
cd ..\project && npm run build && git status
```

Скрипт перехватывает ввод через PSReadLine и автоматически превращает такие команды в корректный PowerShell-код перед выполнением.

## Что поддерживается

- `cmd1 && cmd2` → `cmd1 ; if ($?) { cmd2 }`
- `cmd1 || cmd2` → `cmd1 ; if (-not $?) { cmd2 }`
- Длинные и смешанные цепочки любой длины
- `cmd |& other` → `cmd 2>&1 | other` (pipe + stderr)
- `cmd &> file` / `cmd >& file` → `cmd *> file`
- `cmd &>> file` → `cmd *>> file`

При этом `2>&1` и стандартные перенаправления остаются без изменений.

## Зависимости

- Windows PowerShell 5.1 (встроен в Windows 10 и 11)
- Модуль **PSReadLine** (присутствует по умолчанию на современных системах)

Дополнительных пакетов устанавливать не нужно.

## Быстрая установка

```powershell
# Перейди в папку с инструментом
cd X:\LocalRepo\leak-data-importer\posh-bash-chaining

# Запусти установщик (добавит загрузку в твой профиль)
.\Install.ps1
```

После этого при следующем запуске PowerShell инструмент будет подключаться автоматически.

## Ручное подключение

Если не хочешь менять профиль глобально:

```powershell
. .\Enable-BashChaining.ps1
```

Можно добавить эту строку в `$PROFILE`.

## Отключение

```powershell
Disable-BashChaining
```

## Полезные команды после подключения

- `Get-BashChainingStatus` — статус инструмента
- `$global:BashChainingDebug = $true` — показывать, во что переписались команды

## Структура проекта

```
posh-bash-chaining/
├── Enable-BashChaining.ps1   # Основной скрипт
├── Install.ps1               # Установщик в профиль PowerShell
├── README.md
└── ...
```

## Лицензия

MIT

---

Сделано для комфортной работы на Windows без необходимости сразу переходить на PowerShell 7+.