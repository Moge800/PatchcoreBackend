# ============================================================
# benchmark.ps1 - ベンチマークテスト実行
# 用途: 推論速度・スループットの計測
# ============================================================

# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

$python = ".\.venv\Scripts\python.exe"
$testFile = "tests\benchmark_test.py"

if (-not (Test-Path $python)) {
    Write-Host "[ERROR] Python が見つかりません: $python" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $testFile)) {
    Write-Host "[ERROR] テストファイルが見つかりません: $testFile" -ForegroundColor Red
    exit 1
}

$process = Start-Process -FilePath $python -ArgumentList $testFile -NoNewWindow -PassThru
$process | Wait-Process