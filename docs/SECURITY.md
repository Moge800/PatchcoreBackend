# セキュリティガイドライン

## 本番環境での推奨事項

### 1. 認証の実装

現在、APIには認証機構がありません。本番環境では必ず実装してください。

**推奨実装:**

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.post("/predict")
async def predict(
    api_key: str = Depends(verify_api_key),
    file: UploadFile = File(...)
):
    # ...
```

### 2. CORS設定

必要な場合のみ、特定のオリジンを許可してください。

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 3. レート制限

DoS攻撃を防ぐため、レート制限を実装してください。

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(...):
    # ...
```

### 4. ファイルアップロードの制限

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

async def validate_file(file: UploadFile):
    # サイズチェック
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")
    
    # 拡張子チェック
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")
    
    # ファイルポインタを戻す
    await file.seek(0)
```

### 5. ログの適切な管理

機密情報をログに出力しないようにしてください。

```python
# ❌ 悪い例
logger.info(f"API Key: {api_key}")

# ✓ 良い例
logger.info(f"API Key: {'*' * 10}")
```

### 6. 環境変数の使用

設定情報をハードコードせず、環境変数を使用してください。

```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
```

### 7. HTTPS の使用

本番環境では必ずHTTPSを使用してください。

```bash
# Nginxリバースプロキシの例
server {
    listen 443 ssl;
    server_name api.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### 8. エラーメッセージの慎重な扱い

本番環境では詳細なエラーメッセージを返さないようにしてください。

```python
try:
    result = engine.predict(image)
    return result
except Exception as e:
    if DEBUG:
        # 開発環境: 詳細表示
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))
    else:
        # 本番環境: 一般的なメッセージ
        logger.error(f"Prediction error: {e}")
        raise HTTPException(500, detail="Internal server error")
```

### 9. 入力検証

すべてのユーザー入力を検証してください。

```python
from pydantic import BaseModel, validator

class PredictRequest(BaseModel):
    detail_level: str = "basic"
    
    @validator('detail_level')
    def validate_detail_level(cls, v):
        if v not in ["basic", "full"]:
            raise ValueError("Invalid detail_level")
        return v
```

### 10. 依存関係の定期更新

セキュリティパッチを適用するため、定期的に依存関係を更新してください。

```bash
# 脆弱性チェック
pip install safety
safety check

# 更新可能なパッケージ確認
pip list --outdated
```

---

## セキュリティチェックリスト

- [ ] API認証の実装
- [ ] HTTPS の使用
- [ ] CORS の適切な設定
- [ ] レート制限の実装
- [ ] ファイルアップロードの制限
- [ ] 環境変数の使用
- [ ] ログの適切な管理
- [ ] エラーメッセージの最小化
- [ ] 入力検証の実装
- [ ] 依存関係のセキュリティチェック
- [ ] 定期的なバックアップ
- [ ] アクセスログの監視

---

## インシデント対応

セキュリティインシデントが発生した場合：

1. **即座にサービスを停止**
2. **影響範囲を特定**
3. **ログを保存**
4. **脆弱性を修正**
5. **セキュリティパッチを適用**
6. **監視を強化**

---

## 参考資料

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
