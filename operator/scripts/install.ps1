[CmdletBinding()]
param(
    [switch]$InstallStartupTask
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$OperatorRoot = Split-Path -Parent $PSScriptRoot
Set-Location $OperatorRoot

function Find-Python {
    foreach ($candidate in @("py", "python")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            try {
                $version = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
                if ([version]$version -ge [version]"3.11") { return $candidate }
            } catch {}
        }
    }
    throw "Python 3.11 or newer is required. Install it from python.org, then rerun this script."
}

$Python = Find-Python
if (-not (Test-Path ".venv")) { & $Python -m venv .venv }
$VenvPython = Join-Path $OperatorRoot ".venv\Scripts\python.exe"
$VenvVictor = Join-Path $OperatorRoot ".venv\Scripts\victor-operator.exe"

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e "."
& $VenvPython -m playwright install chromium

if (-not (Test-Path ".env")) { & $VenvVictor init --directory $OperatorRoot }

$RunScript = Join-Path $PSScriptRoot "run.ps1"
if ($InstallStartupTask) {
    $TaskName = "VictorOperator"
    $TaskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$RunScript`""
    schtasks.exe /Create /F /SC ONLOGON /TN $TaskName /TR $TaskCommand | Out-Host
    Write-Host "Installed startup task: $TaskName" -ForegroundColor Green
}

Write-Host "Victor Operator installed." -ForegroundColor Green
Write-Host "Start it with: powershell -ExecutionPolicy Bypass -File `"$RunScript`""
Write-Host "Then open: http://127.0.0.1:8765"
