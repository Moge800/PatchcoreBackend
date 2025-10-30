# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

$python = ".\.venv\Scripts\python.exe"

$process = Start-Process -FilePath $python -ArgumentList "tests\benchmark_test.py" -NoNewWindow -PassThru
$process | Wait-Process