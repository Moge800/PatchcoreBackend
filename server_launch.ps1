# utf-8 do not use BOM

$env:PYTHONPATH = (Resolve-Path ".").Path
$python = ".\.venv\Scripts\python.exe"
$module = "src.api.core.patchcore_api:app"

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

$apiHost = $env:API_SERVER_HOST
$apiPort = $env:API_SERVER_PORT

$clientHost = $env:API_CLIENT_HOST
$clientPort = $env:API_CLIENT_PORT

Write-Host "Starting API Server on ${apiHost}:${apiPort}..."

$process = Start-Process -FilePath $python -ArgumentList "-m uvicorn $module --host $apiHost --port $apiPort --workers 1" -NoNewWindow -PassThru

$maxWait = 20
for ($i = 0; $i -lt $maxWait; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://${clientHost}:${clientPort}/status" -TimeoutSec 2
        if ($response.status -eq "ok") {
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

# Wait for the server process to exit so the $process variable is actually used
$process | Wait-Process
