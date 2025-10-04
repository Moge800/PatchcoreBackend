# API リファレンス

## ベースURL

```
http://localhost:8000
```

## 認証

現在、認証は実装されていません。本番環境では適切な認証機構を追加してください。

---

## エンドポイント

### 1. 異常検知推論

異常検知を実行します。

**エンドポイント:** `POST /predict`

**パラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| file | File | Yes | - | 検査対象の画像ファイル（PNG/JPG） |
| detail_level | string | No | "basic" | 詳細レベル（"basic" または "full"） |

**レスポンス:**

```json
{
  "label": "OK",
  "process_time": 0.035,
  "image_id": {
    "original": "org_OK_20251004082015_6ce6",
    "overlay": "ovr_OK_20251004082015_6ce6"
  },
  "thresholds": {
    "z_score": 3.0,
    "z_area": 0.01,
    "z_max": 5.0
  },
  "z_stats": {
    "area": 0.005,
    "maxval": 4.2
  }
}
```

**使用例:**

```bash
curl -X POST "http://localhost:8000/predict?detail_level=basic" \
  -F "file=@test_image.png"
```

```python
import requests

with open("test_image.png", "rb") as f:
    response = requests.post(
        "http://localhost:8000/predict",
        files={"file": f},
        params={"detail_level": "basic"}
    )
    
result = response.json()
print(f"判定: {result['label']}")
```

---

### 2. 画像取得

キャッシュされた画像を取得します。

**エンドポイント:** `GET /get_image`

**パラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| image_id | string | Yes | 画像ID（predict レスポンスから取得） |

**レスポンス:**

PNG画像データ（バイナリ）

**使用例:**

```bash
curl "http://localhost:8000/get_image?image_id=org_OK_20251004082015_6ce6" \
  -o result.png
```

```python
response = requests.get(
    "http://localhost:8000/get_image",
    params={"image_id": "org_OK_20251004082015_6ce6"}
)

with open("result.png", "wb") as f:
    f.write(response.content)
```

---

### 3. 画像リスト取得

キャッシュされた画像IDのリストを取得します。

**エンドポイント:** `GET /get_image_list`

**パラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| limit | integer | No | 100 | 取得する画像数（1-1000） |
| prefix | string | No | - | プレフィックスフィルタ（"org" または "ovr"） |
| label | string | No | - | ラベルフィルタ（"OK" または "NG"） |
| reverse_list | boolean | No | false | リストを逆順にする |

**レスポンス:**

```json
{
  "image_list": [
    "org_OK_20251004082015_6ce6",
    "ovr_OK_20251004082015_6ce6",
    "org_NG_20251004082015_8d9c",
    "ovr_NG_20251004082015_8d9c"
  ]
}
```

**使用例:**

```bash
# NG画像のみ取得
curl "http://localhost:8000/get_image_list?label=NG&limit=10"

# オーバーレイ画像のみ取得
curl "http://localhost:8000/get_image_list?prefix=ovr&limit=50"
```

---

### 4. ステータス確認

サーバーの状態を確認します。

**エンドポイント:** `GET /status`

**レスポンス:**

```json
{
  "status": "ok",
  "model": "example_model",
  "image_cache": 438
}
```

**使用例:**

```bash
curl "http://localhost:8000/status"
```

---

### 5. GPU情報取得

GPU環境の情報を取得します。

**エンドポイント:** `GET /gpu_info`

**レスポンス:**

```json
{
  "cuda_available": true,
  "gpu_count": 1,
  "current_device": "cuda:0",
  "memory": {
    "allocated": "0.00GB",
    "cached": "0.03GB"
  },
  "gpu_names": ["NVIDIA GeForce RTX 3090"],
  "cuda_version": "12.4"
}
```

---

### 6. システム情報取得

システム環境の情報を取得します。

**エンドポイント:** `GET /system_info`

**レスポンス:**

```json
{
  "platform": "Windows-11-10.0.26100-SP0",
  "cpu_count": 16,
  "memory_total": "68.6GB",
  "memory_available": "45.2GB",
  "pytorch_version": "2.6.0+cu124",
  "cuda_support": true
}
```

---

### 7. エンジン再起動

推論エンジンを再起動します（設定変更後に実行）。

**エンドポイント:** `POST /restart_engine`

**パラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| execute | boolean | No | false | 実際に再起動するか |

**レスポンス:**

```json
{
  "status": "reloaded",
  "model": "example_model"
}
```

**使用例:**

```bash
curl -X POST "http://localhost:8000/restart_engine?execute=true"
```

---

### 8. 画像キャッシュクリア

メモリ内の画像キャッシュをクリアします。

**エンドポイント:** `POST /clear_image`

**パラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| execute | boolean | No | false | 実際にクリアするか |

**レスポンス:**

```json
{
  "status": "cleared"
}
```

---

## エラーレスポンス

エラー時は以下の形式でレスポンスが返されます：

```json
{
  "status": "error",
  "message": "Engine not initialized",
  "error": "詳細なエラーメッセージ"
}
```

**HTTPステータスコード:**

| コード | 説明 |
|--------|------|
| 200 | 成功 |
| 404 | リソースが見つからない |
| 500 | サーバー内部エラー |
| 503 | サービス利用不可（エンジン未初期化） |

---

## レート制限

現在、レート制限は実装されていません。本番環境では適切なレート制限を実装してください。

---

## バージョニング

現在のAPIバージョン: v1

将来的にバージョニングが必要になった場合は、`/v1/predict` のような形式で実装予定です。
