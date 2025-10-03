$env:PYTHONPATH = (Resolve-Path ".").Path
$python = ".\.venv\Scripts\python.exe"
$module = "src.api.core.patchcore_api:app"

# サーバー起動（uvicorn CLI）
$process = Start-Process -FilePath $python -ArgumentList "-m uvicorn $module --host 0.0.0.0 --port 8000 --workers 1" -NoNewWindow -PassThru

# サーバー起動確認（最大10秒待機）
$maxWait = 20
for ($i = 0; $i -lt $maxWait; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/status" -TimeoutSec 2
        if ($response.status -eq "ok") {
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

# GUI起動
# & $python -c "from src.ui.main_gui_launcher import launch_gui; launch_gui()"