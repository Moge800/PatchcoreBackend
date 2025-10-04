#!/bin/bash

# .venv をアクティベート
source .venv/bin/activate

# モジュール検索パスを設定
export PYTHONPATH=$(pwd)

# .env から環境変数を読み込み
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# API_PORT を取得（デフォルト8000）
API_PORT=${API_PORT:-8000}
API_HOST=${API_HOST:-0.0.0.0}

echo "Starting API Server on ${API_HOST}:${API_PORT}..."

# FastAPI サーバーをバックグラウンド起動（uvicorn CLI使用）
python -m uvicorn src.api.core.patchcore_api:app --host $API_HOST --port $API_PORT --workers 1 &
SERVER_PID=$!

# /status エンドポイントで起動確認（最大10秒）
for i in {1..20}; do
    STATUS=$(curl -s http://localhost:${API_PORT}/status | grep -o '"status":"ok"')
    if [ "$STATUS" = '"status":"ok"' ]; then
        break
    fi
    sleep 0.5
done

# GUI 起動
# python -c "from src.ui.main_gui_launcher import launch_gui; launch_gui()"

# サーバープロセスを待機（GUI終了後に自動終了）
wait $SERVER_PID