# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir
Write-Host "Current Directory: $(Get-Location)"
Write-Host "Python exists: $(Test-Path '.\.venv\Scripts\python.exe')"
Write-Host "Tests directory exists: $(Test-Path '.\tests')"
