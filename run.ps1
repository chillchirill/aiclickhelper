param(
    [string]$Python = "python",
    [string]$VenvPath = ".venv",
    [string]$EnvFile = ".env"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Import-DotEnv {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Write-Step "Завантажую змінні з $Path"

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ([string]::IsNullOrWhiteSpace($line)) { return }
        if ($line.StartsWith("#")) { return }

        $parts = $line -split "=", 2
        if ($parts.Count -ne 2) { return }

        $name = $parts[0].Trim()
        $value = $parts[1].Trim()

        if (-not [string]::IsNullOrWhiteSpace($name)) {
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

Write-Step "Перевіряю Python"
& $Python --version

if (-not (Test-Path $VenvPath)) {
    Write-Step "Створюю virtual environment"
    & $Python -m venv $VenvPath
}

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvPip = Join-Path $VenvPath "Scripts\pip.exe"

Write-Step "Оновлюю pip"
& $VenvPython -m pip install --upgrade pip

Write-Step "Ставлю залежності"
& $VenvPip install -r requirements.txt

Import-DotEnv -Path $EnvFile

if (-not $env:OPENAI_API_KEY) {
    Write-Host ""
    Write-Host "OPENAI_API_KEY не знайдено в середовищі." -ForegroundColor Yellow
    $ApiKey = Read-Host "Введи OPENAI_API_KEY"
    if ([string]::IsNullOrWhiteSpace($ApiKey)) {
        throw "Порожній OPENAI_API_KEY. Запуск зупинено."
    }
    $env:OPENAI_API_KEY = $ApiKey
}

Write-Step "Запускаю застосунок"
& $VenvPython main.py
