$env:PYTHONPATH = (Resolve-Path ".").Path
$python = ".\.venv\Scripts\python.exe"
$module = "src.api.core.patchcore_api:app"

# .envから環境変数を読み込み
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# API_PORTを取得（デフォルト8000）
$apiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$apiHost = if ($env:API_HOST) { $env:API_HOST } else { "0.0.0.0" }

Write-Host "Starting API Server on ${apiHost}:${apiPort}..."

# サーバー起動（uvicorn CLI）
$process = Start-Process -FilePath $python -ArgumentList "-m uvicorn $module --host $apiHost --port $apiPort --workers 1" -NoNewWindow -PassThru

# サーバー起動確認（最大10秒待機）
$maxWait = 20
for ($i = 0; $i -lt $maxWait; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:${apiPort}/status" -TimeoutSec 2
        if ($response.status -eq "ok") {
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

# GUI起動
# & $python -c "from src.ui.main_gui_launcher import launch_gui; launch_gui()"