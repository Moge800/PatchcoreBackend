# API設定ガイド

## サーバーとクライアントの設定分離

v2.0以降、APIサーバーとクライアントの設定が分離されました。

### 🔧 設定項目

#### サーバー設定（バインドアドレス）

| 変数名 | 説明 | デフォルト値 | 用途 |
|--------|------|-------------|------|
| `API_SERVER_HOST` | サーバーがバインドするアドレス | `0.0.0.0` | サーバー起動時に使用 |
| `API_SERVER_PORT` | サーバーがリッスンするポート | `8000` | サーバー起動時に使用 |

**API_SERVER_HOSTの設定値**:
- `0.0.0.0`: すべてのネットワークインターフェースでリッスン（外部アクセス可能）
- `127.0.0.1`: ローカルループバックのみ（外部アクセス不可、セキュア）

#### クライアント設定（接続先アドレス）

| 変数名 | 説明 | デフォルト値 | 用途 |
|--------|------|-------------|------|
| `API_CLIENT_HOST` | クライアントが接続する先のアドレス | `127.0.0.1` | APIクライアントが使用 |
| `API_CLIENT_PORT` | クライアントが接続する先のポート | `8000` | APIクライアントが使用 |

**API_CLIENT_HOSTの設定値**:
- `127.0.0.1` または `localhost`: ローカルサーバーに接続
- `192.168.x.x`: LAN内の特定サーバーに接続
- 外部IP: インターネット越しのサーバーに接続

### 📝 設定例

#### ケース1: ローカル開発（デフォルト）

```properties
# .env
API_SERVER_HOST=0.0.0.0    # すべてのインターフェースでリッスン
API_SERVER_PORT=8000

API_CLIENT_HOST=127.0.0.1  # ローカルサーバーに接続
API_CLIENT_PORT=8000
```

**動作**:
- サーバー: `0.0.0.0:8000` でリッスン
- クライアント: `127.0.0.1:8000` に接続
- 結果: ローカルで動作、外部からもアクセス可能

#### ケース2: セキュアなローカル環境

```properties
# .env
API_SERVER_HOST=127.0.0.1  # ローカルのみでリッスン
API_SERVER_PORT=8000

API_CLIENT_HOST=127.0.0.1
API_CLIENT_PORT=8000
```

**動作**:
- サーバー: `127.0.0.1:8000` でリッスン（外部アクセス不可）
- クライアント: `127.0.0.1:8000` に接続
- 結果: 完全にローカルのみ、最もセキュア

#### ケース3: LAN内のリモートサーバー

```properties
# .env（サーバー側）
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8000

# .env（クライアント側）
API_CLIENT_HOST=192.168.1.100  # サーバーのIPアドレス
API_CLIENT_PORT=8000
```

**動作**:
- サーバー: `0.0.0.0:8000` でリッスン
- クライアント: `192.168.1.100:8000` に接続
- 結果: LAN内の他のマシンからアクセス可能

### 🔄 後方互換性

旧変数名（`API_HOST`, `API_PORT`）も引き続き使用可能です：

```python
# env_loader.py
API_HOST = API_CLIENT_HOST  # 旧名称（非推奨）
API_PORT = API_CLIENT_PORT  # 旧名称（非推奨）
```

既存のコードは修正不要ですが、新しいコードでは以下を推奨：
- サーバー側: `API_SERVER_HOST`, `API_SERVER_PORT`
- クライアント側: `API_CLIENT_HOST`, `API_CLIENT_PORT`

### 🚀 サーバー起動

起動スクリプトは自動的に新しい変数名を使用します：

```powershell
# PowerShell
.\server_launch.ps1
```

```bash
# Linux/Mac
./server_launch.sh
```

起動時に表示されるメッセージで確認：
```
Starting API Server on 0.0.0.0:8000...
```

### 🧪 テスト

```python
# クライアントコード例
from src.api.client.patchcore_api_client import PatchCoreApiClient

# デフォルト（.envから自動取得）
client = PatchCoreApiClient()

# カスタムURL指定
client = PatchCoreApiClient(base_url="http://192.168.1.100:8000")
```

### 📚 関連ドキュメント

- [ENV_GUIDE.md](ENV_GUIDE.md) - 環境変数の詳細
- [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md) - 設定管理の全体像
- [API.md](API.md) - API仕様
