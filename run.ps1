param([int]$Port = 8501)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$taskBundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $taskPython) {
    & $taskPython src --port $Port
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python src --port $Port
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 src --port $Port
} elseif (Test-Path -LiteralPath $taskBundledPython) {
    & $taskBundledPython src --port $Port
} else {
    Write-Error 'Install Python 3.10 or newer, then run: python src'
}
