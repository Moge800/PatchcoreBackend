# サーバー操作ガイド

PatchCore バックエンドサーバーの起動・モデル管理・推論の手順をまとめた取説です。

---

## 目次

1. [前提条件](#1-前提条件)
2. [サーバーの起動と停止](#2-サーバーの起動と停止)
3. [モデル管理](#3-モデル管理)
4. [推論の実行（ジョブキュー）](#4-推論の実行ジョブキュー)
5. [画像キャッシュの操作](#5-画像キャッシュの操作)
6. [環境変数による起動設定](#6-環境変数による起動設定)
7. [Python クライアントの使い方](#7-python-クライアントの使い方)
8. [よくある操作フロー](#8-よくある操作フロー)
9. [トラブルシューティング](#9-トラブルシューティング)

---

## 1. 前提条件

- Python 3.10 以上
- 依存パッケージのインストール済み（`pip install -e .`）
- `models/` 以下にモデルファイルが存在すること
- `.env` ファイルが存在すること（なければ `.env.example` からコピー）

```bash
# .env を作成
copy .env.example .env   # Windows
cp .env.example .env     # Linux / Mac
```

---

## 2. サーバーの起動と停止

### 起動

```bash
# 標準起動
uvicorn src.api.core.patchcore_api:app --host 0.0.0.0 --port 8000

# ホットリロード付き（開発時）
uvicorn src.api.core.patchcore_api:app --reload --port 8000

# PYTHONPATH を通す必要がある場合
PYTHONPATH=. uvicorn src.api.core.patchcore_api:app --port 8000
```

起動確認（別ターミナルで）:

```bash
curl http://localhost:8000/system_info
```

`platform` などが返ってくれば正常起動です。

### 停止

ターミナルで `Ctrl + C`。

### 起動時モデルの自動ロード

`.env` の `LOADED_MODELS` にカンマ区切りでモデル名を書いておくと、起動時に自動ロードされます。

```ini
# .env
LOADED_MODELS=example_model
# 複数の場合:
# LOADED_MODELS=example_model,model_b
```

---

## 3. モデル管理

サーバー起動中はいつでもモデルの追加・削除が可能です。

### 3-1. モデル一覧の確認

```bash
curl http://localhost:8000/models
```

```json
{
  "models": [
    { "name": "example_model", "status": "loaded",   "loaded_at": "2026-03-28T10:00:00" },
    { "name": "model_b",       "status": "unloaded", "loaded_at": null }
  ]
}
```

`status` が `loaded` のモデルのみ推論できます。

### 3-2. モデルをロードする

```bash
curl -X POST http://localhost:8000/models/example_model/load
```

モデルのロードには数秒〜数十秒かかります（GPU メモリへの転送があるため）。
ロード中は他のリクエストも並行して受け付けます。

### 3-3. モデルのステータスを確認する

```bash
curl http://localhost:8000/models/example_model/status
```

```json
{
  "name": "example_model",
  "status": "loaded",
  "device": "cuda:0",
  "image_cache": 42
}
```

### 3-4. モデルをアンロードする（ファイルは残す）

```bash
curl -X DELETE http://localhost:8000/models/example_model/unload
```

GPU メモリが解放されます。ファイルは `models/` に残るため、再ロードできます。

### 3-5. モデルを完全削除する

> **注意:** `models/{name}/` と `settings/models/{name}/` が**完全に削除されます。元に戻せません。**

```bash
curl -X DELETE http://localhost:8000/models/example_model
```

---

## 4. 推論の実行（ジョブキュー）

推論は非同期ジョブとして処理されます。

### フロー

```
① 推論ジョブ投入
   POST /models/{name}/predict
        ↓ job_id を受け取る（即返却）

② 結果のポーリング
   GET /jobs/{job_id}
        ↓ status = "completed" になるまで繰り返す

③ 結果取得
   result.label = "OK" or "NG"
```

### Step 1: ジョブを投入する

```bash
curl -X POST "http://localhost:8000/models/example_model/predict" \
  -F "file=@test_image.png"
```

```json
{
  "job_id": "a1b2c3d4e5f67890abcdef12",
  "status": "pending"
}
```

`detail_level=full` にすると閾値情報も返ります:

```bash
curl -X POST "http://localhost:8000/models/example_model/predict?detail_level=full" \
  -F "file=@test_image.png"
```

### Step 2: 結果をポーリングする

```bash
curl http://localhost:8000/jobs/a1b2c3d4e5f67890abcdef12
```

**処理中:**
```json
{ "job_id": "...", "status": "running" }
```

**完了:**
```json
{
  "job_id": "...",
  "status": "completed",
  "result": {
    "label": "OK",
    "image_id": {
      "original": "org_OK_20260328100000_a1b2",
      "overlay":  "ovr_OK_20260328100000_a1b2"
    },
    "z_stats": { "area": 15, "maxval": 2.8 }
  }
}
```

### ジョブ一覧の確認

```bash
# 全ジョブ
curl http://localhost:8000/jobs

# 特定モデルの完了ジョブだけ
curl "http://localhost:8000/jobs?model_name=example_model&status=completed&limit=20"
```

### ジョブの保持時間

完了・失敗したジョブは `.env` の `JOB_QUEUE_TTL`（デフォルト 3600 秒）を過ぎると自動削除されます。

---

## 5. 画像キャッシュの操作

推論実行後、入力画像とヒートマップ重畳画像がサーバーメモリにキャッシュされます。

### キャッシュされた画像 ID を取得する

```bash
# 全画像
curl http://localhost:8000/models/example_model/images

# NG 画像のオーバーレイのみ
curl "http://localhost:8000/models/example_model/images?label=NG&prefix=ovr"
```

### 画像をダウンロードする

```bash
# image_id は推論結果 result.image_id から取得
curl "http://localhost:8000/models/example_model/images/org_OK_20260328100000_a1b2" \
  -o original.png

curl "http://localhost:8000/models/example_model/images/ovr_OK_20260328100000_a1b2" \
  -o overlay.png
```

画像 ID の形式:

| プレフィックス | 内容 |
|--------------|------|
| `org_` | 元の入力画像 |
| `ovr_` | ヒートマップ重畳画像 |

### キャッシュをクリアする

```bash
curl -X POST "http://localhost:8000/models/example_model/images/clear?execute=true"
```

`execute=true` をつけないと実行されません（誤操作防止）。

---

## 6. 環境変数による起動設定

`.env` で以下の値を設定できます。詳細は [ENV_GUIDE.md](ENV_GUIDE.md) を参照。

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `API_SERVER_HOST` | `0.0.0.0` | バインドアドレス（`127.0.0.1` にするとローカルのみ）|
| `API_SERVER_PORT` | `8000` | ポート番号 |
| `LOADED_MODELS` | `""` | 起動時にロードするモデル（カンマ区切り）|
| `JOB_QUEUE_TTL` | `3600` | 完了ジョブの保持時間（秒）|
| `USE_GPU` | `False` | GPU を使うか（推奨: `True`）|
| `GPU_DEVICE_ID` | `0` | 使用する GPU の番号 |
| `LOG_LEVEL` | `INFO` | ログレベル（`DEBUG` / `INFO` / `WARNING`）|
| `MAX_CACHE_IMAGES` | `1200` | 1 モデルあたりの画像キャッシュ上限枚数 |

---

## 7. Python クライアントの使い方

`src/api/client/patchcore_api_client.py` で提供されるクライアントクラスを使うと、HTTP の詳細を意識せずに操作できます。

### 基本的な使い方

```python
from src.api.client.patchcore_api_client import PatchCoreApiClient
import cv2

client = PatchCoreApiClient()  # env_loader から URL 自動取得

# サーバー起動待ち
if not client.wait_for_server(max_wait=30):
    raise RuntimeError("サーバーが起動していません")

# モデルをロード
client.load_model("example_model")

# 推論（同期・ポーリングを内包）
img = cv2.imread("test.jpg")
result = client.predict("example_model", img, detail_level="basic")

print(result["label"])       # "OK" or "NG"
print(result["z_stats"])     # area, maxval

# 画像を取得
ovr = client.fetch_image("example_model", result["image_id"]["overlay"])
cv2.imwrite("overlay.png", ovr)
```

### 非同期（submit + poll）パターン

`predict()` が内部でやっていることを手動で行う場合:

```python
# ジョブ投入
job_id = client.submit_predict("example_model", img)

# 任意のタイミングでポーリング
import time
while True:
    job = client.poll_job(job_id)
    if job["status"] in ("completed", "failed"):
        break
    time.sleep(0.2)

if job["status"] == "completed":
    print(job["result"])
```

### 主なメソッド一覧

| メソッド | 説明 |
|---------|------|
| `list_models()` | モデル一覧取得 |
| `load_model(name)` | モデルロード |
| `unload_model(name)` | モデルアンロード |
| `model_status(name)` | モデルステータス確認 |
| `predict(name, img)` | 推論（同期ラッパー）|
| `submit_predict(name, img)` | ジョブ投入（`job_id` を返す）|
| `poll_job(job_id)` | ジョブ状態取得 |
| `list_jobs(...)` | ジョブ一覧取得 |
| `fetch_image_list(name)` | 画像 ID 一覧取得 |
| `fetch_image(name, image_id)` | 画像取得（ndarray）|
| `clear_image_cache(name)` | 画像キャッシュクリア |
| `fetch_system_info()` | システム情報取得 |
| `fetch_gpu_info()` | GPU 情報取得 |

---

## 8. よくある操作フロー

### 初回セットアップ

```bash
# 1. .env 作成
cp .env.example .env

# 2. .env 編集（USE_GPU, DEFAULT_MODEL_NAME など）

# 3. サーバー起動
uvicorn src.api.core.patchcore_api:app --port 8000

# 4. モデルロード
curl -X POST http://localhost:8000/models/example_model/load

# 5. 推論テスト
python tests/predict_test.py
```

### モデルを切り替える

```bash
# 現在ロードされているモデルを確認
curl http://localhost:8000/models

# 旧モデルをアンロード（メモリ解放）
curl -X DELETE http://localhost:8000/models/old_model/unload

# 新モデルをロード
curl -X POST http://localhost:8000/models/new_model/load
```

### 複数モデルを同時に使う

```bash
# 複数モデルを順番にロード
curl -X POST http://localhost:8000/models/model_a/load
curl -X POST http://localhost:8000/models/model_b/load

# それぞれに推論リクエストを投げる
curl -X POST http://localhost:8000/models/model_a/predict -F "file=@img_a.png"
curl -X POST http://localhost:8000/models/model_b/predict -F "file=@img_b.png"
```

ジョブはシングルワーカーで順番に処理されます。並行リクエストは内部でキューに積まれます。

---

## 9. トラブルシューティング

### サーバーが起動しない

**症状:** `uvicorn` コマンドがエラーで落ちる

**確認事項:**
- `PYTHONPATH=.` が設定されているか
- `.env` ファイルが存在するか
- ポート 8000 が他プロセスに使われていないか（`netstat -ano | findstr 8000`）

---

### モデルロードが 404 になる

```json
{ "error": "... No such file or directory ..." }
```

**確認事項:**
- `models/{model_name}/` ディレクトリが存在するか
- `settings/models/{model_name}/settings.py` が存在するか
- モデル名のスペルミスがないか（大文字小文字を区別します）

---

### 推論ジョブが `failed` になる

```bash
curl http://localhost:8000/jobs/{job_id}
# → "status": "failed", "error": "..."
```

**よくある原因:**

| エラー内容 | 原因と対処 |
|-----------|-----------|
| `Model 'xxx' is not loaded` | モデルがアンロードされた。再ロードしてください |
| `CUDA out of memory` | GPU メモリ不足。他モデルをアンロードするか CPU 推論に切り替え |
| `image decode error` | 対応していない画像形式。PNG / JPG を使用してください |

---

### ジョブが `pending` のまま進まない

**原因:** ワーカーが前のジョブを処理中です。シングルワーカーのため、キューは順番に処理されます。

`GET /jobs?status=running` で現在処理中のジョブを確認してください。

---

### GPU が使われない

`.env` を確認してください:

```ini
USE_GPU=True
GPU_DEVICE_ID=0
```

その後、モデルを一度アンロードして再ロードします:

```bash
curl -X DELETE http://localhost:8000/models/example_model/unload
curl -X POST  http://localhost:8000/models/example_model/load
```

`GET /models/example_model/status` で `"device": "cuda:0"` になっていれば GPU 使用中です。

---

### ログの確認

```
logs/
  api/        # サーバーとルーターのログ
  inference/  # 推論エンジンのログ
  model/      # モデル学習のログ
```

リアルタイム確認:

```bash
# Windows PowerShell
Get-Content logs/api/patchcore_api.log -Wait

# Linux / Mac
tail -f logs/api/patchcore_api.log
```

---

## 📚 関連ドキュメント

- [INDEX.md](INDEX.md) - ドキュメント一覧
- [API.md](API.md) - REST API エンドポイント仕様
- [ENV_GUIDE.md](ENV_GUIDE.md) - 環境変数の設定リファレンス
- [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md) - 設定管理の全体像
