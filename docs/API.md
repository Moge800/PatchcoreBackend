# API リファレンス

## ベース URL

```
http://localhost:8000
```

## 認証

なし（ローカル運用想定）

---

## エンドポイント一覧

| カテゴリ | Method | Path | 説明 |
|---------|--------|------|------|
| Models | GET | `/models` | モデル一覧 |
| Models | GET | `/models/{name}/status` | モデルステータス |
| Models | POST | `/models/{name}/load` | モデルをロード |
| Models | DELETE | `/models/{name}/unload` | メモリからアンロード |
| Models | DELETE | `/models/{name}` | アンロード + ファイル削除 |
| Inference | POST | `/models/{name}/predict` | 推論ジョブ投入 |
| Jobs | GET | `/jobs/{job_id}` | ジョブ状態・結果取得 |
| Jobs | GET | `/jobs` | ジョブ一覧 |
| Images | GET | `/models/{name}/images` | 画像ID一覧 |
| Images | GET | `/models/{name}/images/{image_id}` | 画像取得（PNG）|
| Images | POST | `/models/{name}/images/clear` | キャッシュクリア |
| System | GET | `/system_info` | OS・CPU・メモリ情報 |
| System | GET | `/gpu_info` | GPU・CUDA情報 |

---

## Models

### GET /models

利用可能な全モデルをロード状態込みで返す。

**レスポンス例:**
```json
{
  "models": [
    {
      "name": "example_model",
      "status": "loaded",
      "loaded_at": "2026-03-28T10:00:00.123456",
      "error": null
    },
    {
      "name": "model_b",
      "status": "unloaded",
      "loaded_at": null,
      "error": null
    }
  ]
}
```

`status` の値:

| 値 | 意味 |
|----|------|
| `loaded` | メモリにロード済み、推論可能 |
| `unloaded` | ファイルはあるがアンロード済み |

---

### GET /models/{model_name}/status

指定モデルのステータスを返す。ロード済みの場合はデバイスとキャッシュ数も含む。

**レスポンス例（ロード済み）:**
```json
{
  "name": "example_model",
  "status": "loaded",
  "device": "cuda:0",
  "image_cache": 42
}
```

**レスポンス例（未ロード）:**
```json
{
  "name": "example_model",
  "status": "unloaded"
}
```

---

### POST /models/{model_name}/load

モデルをメモリにロードする。モデルファイルは `models/{model_name}/` に必要。

**レスポンス例:**
```json
{
  "status": "loaded",
  "name": "example_model",
  "loaded_at": "2026-03-28T10:00:00.123456"
}
```

**エラーコード:**

| コード | 原因 |
|--------|------|
| 404 | モデルファイルが見つからない |
| 409 | 既にロード済み |
| 500 | ロード中にエラー発生 |

**使用例:**
```bash
curl -X POST http://localhost:8000/models/example_model/load
```

---

### DELETE /models/{model_name}/unload

モデルをメモリからアンロードする。ファイルは削除しない。

**レスポンス例:**
```json
{
  "status": "unloaded",
  "name": "example_model"
}
```

**エラーコード:**

| コード | 原因 |
|--------|------|
| 404 | モデルが未登録 |
| 409 | 既にアンロード済み |

---

### DELETE /models/{model_name}

モデルをアンロードし、`models/{model_name}/` と `settings/models/{model_name}/` を**完全削除**する。

> **注意:** この操作は元に戻せません。

**レスポンス例:**
```json
{
  "status": "deleted",
  "name": "example_model"
}
```

---

## Inference（推論）

推論は**2ステップ**です:

1. `POST /models/{name}/predict` → `job_id` を受け取る
2. `GET /jobs/{job_id}` → `status` が `completed` になるまでポーリング

---

### POST /models/{model_name}/predict

推論ジョブをキューに投入する。**モデルが事前にロードされている必要があります。**

**リクエスト (multipart/form-data):**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| file | File | Yes | - | 検査画像（PNG / JPG）|
| detail_level | string | No | `"basic"` | `"basic"` または `"full"` |

**レスポンス (202 Accepted):**
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "status": "pending"
}
```

**エラーコード:**

| コード | 原因 |
|--------|------|
| 404 | モデルが存在しない |
| 503 | モデルが未ロード |

**使用例:**
```bash
curl -X POST "http://localhost:8000/models/example_model/predict?detail_level=basic" \
  -F "file=@test_image.png"
```

---

## Jobs

### GET /jobs/{job_id}

ジョブの状態と結果を返す。`status` が `pending` / `running` の場合は結果なし。

**レスポンス（処理中）:**
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "model_name": "example_model",
  "status": "running",
  "created_at": "2026-03-28T10:00:00.100000",
  "started_at": "2026-03-28T10:00:00.150000"
}
```

**レスポンス（完了）:**
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "model_name": "example_model",
  "status": "completed",
  "created_at": "2026-03-28T10:00:00.100000",
  "started_at": "2026-03-28T10:00:00.150000",
  "completed_at": "2026-03-28T10:00:00.350000",
  "result": {
    "label": "OK",
    "image_id": {
      "original": "org_OK_20260328100000_a1b2",
      "overlay":  "ovr_OK_20260328100000_a1b2"
    },
    "z_stats": {
      "z_score": 1.2,
      "z_area": 0.003,
      "z_max": 2.8
    }
  }
}
```

`detail_level=full` の場合は `result` に `thresholds` も含まれます。

**レスポンス（失敗）:**
```json
{
  "job_id": "a1b2c3d4e5f6...",
  "model_name": "example_model",
  "status": "failed",
  "created_at": "2026-03-28T10:00:00.100000",
  "completed_at": "2026-03-28T10:00:00.200000",
  "error": "エラーの内容"
}
```

`status` の値:

| 値 | 意味 |
|----|------|
| `pending` | キュー待ち |
| `running` | 推論実行中 |
| `completed` | 完了（`result` あり）|
| `failed` | 失敗（`error` あり）|

---

### GET /jobs

ジョブ一覧を新しい順で返す。

**クエリパラメータ:**

| パラメータ | 型 | デフォルト | 説明 |
|----------|-----|-----------|------|
| model_name | string | - | モデル名でフィルタ |
| status | string | - | ステータスでフィルタ |
| limit | integer | 100 | 最大件数（1-1000）|

**レスポンス例:**
```json
{
  "jobs": [
    {
      "job_id": "a1b2c3d4...",
      "model_name": "example_model",
      "status": "completed",
      "created_at": "2026-03-28T10:00:00",
      "completed_at": "2026-03-28T10:00:00.350000"
    }
  ]
}
```

---

## Images

### GET /models/{model_name}/images

モデルのキャッシュ画像 ID 一覧を返す。

**クエリパラメータ:**

| パラメータ | 型 | デフォルト | 説明 |
|----------|-----|-----------|------|
| limit | integer | 100 | 最大件数（1-1000）|
| prefix | string | - | `"org"` または `"ovr"` でフィルタ |
| label | string | - | `"OK"` または `"NG"` でフィルタ |
| reverse_list | boolean | false | リストを逆順にする |

**レスポンス例:**
```json
{
  "image_list": [
    "org_OK_20260328100000_a1b2",
    "ovr_OK_20260328100000_a1b2",
    "org_NG_20260328100001_c3d4",
    "ovr_NG_20260328100001_c3d4"
  ]
}
```

画像 ID の形式: `{prefix}_{label}_{timestamp}_{hash}`

---

### GET /models/{model_name}/images/{image_id}

キャッシュされた画像を PNG で返す。

**レスポンス:** PNG バイナリ（`Content-Type: image/png`）

**使用例:**
```bash
curl "http://localhost:8000/models/example_model/images/org_OK_20260328100000_a1b2" \
  -o result.png
```

---

### POST /models/{model_name}/images/clear

モデルの画像キャッシュを全削除する。

**クエリパラメータ:**

| パラメータ | 型 | デフォルト | 説明 |
|----------|-----|-----------|------|
| execute | boolean | false | `true` にしないと実行されない（誤操作防止）|

**レスポンス例:**
```json
{ "status": "cleared" }
```

```bash
curl -X POST "http://localhost:8000/models/example_model/images/clear?execute=true"
```

---

## System

### GET /system_info

OS・CPU・メモリ・PyTorch バージョン情報を返す。認証不要。

**レスポンス例:**
```json
{
  "platform": "Windows-11-10.0.26200-SP0",
  "cpu_count": 16,
  "memory_total": "64.0GB",
  "memory_available": "48.3GB",
  "pytorch_version": "2.8.0+cu124",
  "cuda_support": true
}
```

---

### GET /gpu_info

GPU・CUDA 情報を返す。GPU なし環境では `cuda_available: false`。

**レスポンス例:**
```json
{
  "cuda_available": true,
  "cuda_version": "12.4",
  "device_count": 1,
  "current_device": "cuda:0",
  "mixed_precision": true,
  "memory": {
    "allocated": "0.50GB",
    "cached": "0.75GB"
  },
  "gpu_0_properties": {
    "name": "NVIDIA GeForce RTX 3090",
    "total_memory": "24.0GB",
    "multi_processor_count": 82,
    "major": 8,
    "minor": 6
  }
}
```

---

## エラーレスポンス共通形式

```json
{ "error": "エラーの内容" }
```

**主な HTTP ステータスコード:**

| コード | 意味 |
|--------|------|
| 200 | 成功 |
| 202 | 受付済み（推論ジョブ投入）|
| 404 | リソースが見つからない |
| 409 | 競合（例: 既にロード済み）|
| 500 | サーバー内部エラー |
| 503 | モデルが未ロード |
