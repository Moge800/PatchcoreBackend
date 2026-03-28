# ============================================================
# restart_engine.ps1 - 推論エンジン再起動
# 用途: 稼働中の API サーバーの推論エンジンを再起動する
# 前提: API サーバーが起動済みであること
# ============================================================

# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/restart_engine?execute=true" -Method Post
    Write-Host "[OK] エンジン再起動成功" -ForegroundColor Green
    $response | ConvertTo-Json
} catch {
    Write-Host "[ERROR] エンジン再起動失敗: $_" -ForegroundColor Red
    Write-Host "API サーバーが起動しているか確認してください"
}