# ============================================================
# test_paths.ps1 - パス・依存関係の存在確認
# 用途: プロジェクトの主要ファイル・ディレクトリが
#       正しく配置されているか診断する
# ============================================================

# scriptsディレクトリから親ディレクトリに移動
$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$parentDir = Split-Path $scriptDir -Parent
Set-Location $parentDir

Write-Host "=== プロジェクトパスチェック ==="
Write-Host "Working dir:  $(Get-Location)"
Write-Host "Python:       $(if (Test-Path '.\.venv\Scripts\python.exe') { '✅ OK' } else { '❌ 見つかりません' })"
Write-Host "Tests dir:    $(if (Test-Path '.\tests') { '✅ OK' } else { '❌ 見つかりません' })"
Write-Host ".env file:    $(if (Test-Path '.\.env') { '✅ OK' } else { '❌ 見つかりません' })"
Write-Host "Models dir:   $(if (Test-Path '.\models') { '✅ OK' } else { '❌ 見つかりません' })"
Write-Host "Settings dir: $(if (Test-Path '.\settings') { '✅ OK' } else { '❌ 見つかりません' })"
