$ErrorActionPreference = "Stop"
$OperatorRoot = Split-Path -Parent $PSScriptRoot
Set-Location $OperatorRoot
$Victor = Join-Path $OperatorRoot ".venv\Scripts\victor-operator.exe"
if (-not (Test-Path $Victor)) {
    throw "Victor Operator is not installed. Run scripts\install.ps1 first."
}
& $Victor serve
