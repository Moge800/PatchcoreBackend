# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

$response = Invoke-RestMethod -Uri "http://localhost:8000/restart_engine?execute=true" -Method Post