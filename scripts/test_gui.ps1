# ============================================================
# test_gui.ps1 - GUI 実行環境の事前チェック
# 用途: Python と GUI ファイルの存在確認（実行はしない）
# ============================================================

# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

$python = ".\.venv\Scripts\python.exe"
$guiFile = "src\ui\main_gui_launcher.py"

Write-Host "=== GUI 実行環境チェック ==="
Write-Host "Python:   $(if (Test-Path $python) { '✅ OK' } else { '❌ 見つかりません' }) ($python)"
Write-Host "GUI file: $(if (Test-Path $guiFile) { '✅ OK' } else { '❌ 見つかりません' }) ($guiFile)"
Write-Host "Command:  $python $guiFile"
