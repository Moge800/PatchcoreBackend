# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

$python=".\.venv\Scripts\python.exe"
$guiFile="src\ui\main_gui_launcher.py"

Write-Host "Python exists: $(Test-Path $python)"
Write-Host "GUI file exists: $(Test-Path $guiFile)"
Write-Host "Would execute: $python $guiFile"
