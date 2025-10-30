# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

$python=".\.venv\Scripts\python.exe"

$process = Start-Process -FilePath $python "src\ui\main_gui_launcher.py" -NoNewWindow -PassThru

$process | Wait-Process