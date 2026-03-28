# ============================================================
# launch_settings_gui.ps1 - 設定用 GUI 起動スクリプト
# 用途: main_gui_launcher.py を起動し、モデル設定や
#       学習・推論を GUI で操作できるようにする
# ============================================================

# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

$python = ".\.venv\Scripts\python.exe"
$guiFile = "src\ui\main_gui_launcher.py"

if (-not (Test-Path $python)) {
    Write-Host "[ERROR] Python が見つかりません: $python" -ForegroundColor Red
    Write-Host "仮想環境を作成してください: python -m venv .venv"
    exit 1
}
if (-not (Test-Path $guiFile)) {
    Write-Host "[ERROR] GUI ファイルが見つかりません: $guiFile" -ForegroundColor Red
    exit 1
}

$process = Start-Process -FilePath $python -ArgumentList $guiFile -NoNewWindow -PassThru
$process | Wait-Process