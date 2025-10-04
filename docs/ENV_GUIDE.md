# 環境変数システムの使用ガイド

## 概要
`.env`ファイルを使用して、プロジェクト全体の設定を一元管理できるようになりました。

## セットアップ

### 1. .envファイルの作成
```powershell
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2. python-dotenvのインストール
```bash
pip install python-dotenv==1.0.1
```

または、requirements.txtから一括インストール：
```bash
pip install -r requirements.txt
```

## 設定のオーバーライド

### 優先順位
1. `.env`ファイルの環境変数（最優先）
2. `settings/models/{model_name}/settings.py`の設定値
3. デフォルト値

### オーバーライド可能な設定

#### GPU設定
```bash
# .envファイル
USE_GPU=True
GPU_DEVICE_ID=0
USE_MIXED_PRECISION=True
```

settings.pyで`USE_GPU=False`と設定されていても、`.env`で`USE_GPU=True`と指定すれば、GPUが使用されます。

#### ログ設定
```bash
LOG_LEVEL=DEBUG  # INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs
```

#### キャッシュ設定
```bash
MAX_CACHE_IMAGES=1500
NG_IMAGE_SAVE=True
```

#### PCA設定
```bash
PCA_VARIANCE=0.98
```

#### データ拡張
```bash
ENABLE_AUGMENT=True
```

## 使用例

### シナリオ1: 開発環境でGPUをテスト
```bash
# .env
USE_GPU=True
GPU_DEVICE_ID=0
LOG_LEVEL=DEBUG
```

### シナリオ2: 本番環境でCPU実行
```bash
# .env
USE_GPU=False
LOG_LEVEL=INFO
MAX_CACHE_IMAGES=2000
```

### シナリオ3: 複数GPUの切り替え
```bash
# GPU 0を使用
GPU_DEVICE_ID=0

# GPU 1を使用
GPU_DEVICE_ID=1
```

## 環境変数の確認

### Pythonから確認
```python
from src.config import env_loader

# 設定値を表示
env_loader.print_config()
```

### コマンドラインから確認
```bash
python -m src.config.env_loader
```

## 設定可能な環境変数一覧

### アプリケーション設定
- `APP_NAME`: アプリケーション名
- `APP_VERSION`: バージョン
- `DEBUG`: デバッグモード（True/False）

### APIサーバー設定
- `API_HOST`: APIホスト（例: 0.0.0.0）
- `API_PORT`: APIポート（例: 8000）
- `API_RELOAD`: 自動リロード（True/False）
- `API_WORKERS`: ワーカー数

### モデル設定
- `DEFAULT_MODEL_NAME`: デフォルトモデル名

### ログ設定
- `LOG_LEVEL`: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- `LOG_DIR`: ログディレクトリ

### GPU設定
- `USE_GPU`: GPU使用（True/False）
- `GPU_DEVICE_ID`: GPUデバイスID（0, 1, 2...）
- `USE_MIXED_PRECISION`: 混合精度演算（True/False）

### CPU最適化設定
- `CPU_THREADS`: CPUスレッド数
- `CPU_MEMORY_EFFICIENT`: メモリ効率重視（True/False）

### データ設定
- `DATA_DIR`: データセットディレクトリ
- `MODEL_DIR`: モデルディレクトリ
- `SETTINGS_DIR`: 設定ファイルディレクトリ

### キャッシュ設定
- `MAX_CACHE_IMAGES`: 最大キャッシュ画像数
- `CACHE_TTL`: キャッシュTTL（秒）

### NG画像保存設定
- `NG_IMAGE_SAVE`: NG画像保存（True/False）

### セキュリティ設定
- `API_KEY`: APIキー
- `ALLOWED_ORIGINS`: 許可オリジン（カンマ区切り）

### PCA設定
- `PCA_VARIANCE`: PCA分散保持率（0.0〜1.0）

### データ拡張設定
- `ENABLE_AUGMENT`: データ拡張有効化（True/False）

## 注意事項

### .envファイルの管理
- `.env`ファイルは**Gitで管理しない**（`.gitignore`に含まれています）
- 本番環境では`.env.example`をコピーして適切な値を設定してください
- APIキーなどの機密情報は`.env`ファイルで管理してください

### 設定の変更
- `.env`ファイルを変更した場合、アプリケーションの再起動が必要です
- APIサーバーを再起動：`/restart_engine?execute=true`エンドポイント

### トラブルシューティング
- `.env`ファイルが読み込まれない → プロジェクトルートに配置されているか確認
- 環境変数が反映されない → アプリケーションを再起動
- 設定値が期待通りでない → `env_loader.print_config()`で確認

## 統合状況

### ✅ 統合済みモジュール
- `src/api/core/patchcore_api.py`: APIサーバー設定、モデル名
- `src/utils/logger.py`: ログレベル、ログディレクトリ
- `src/config/settings_loader.py`: GPU設定、キャッシュ設定などのオーバーライド
- `settings/main_settings.py`: デフォルトモデル名

### 📋 オーバーライド機能
SettingsLoaderを通じて以下の設定が環境変数でオーバーライド可能：
- `USE_GPU`
- `GPU_DEVICE_ID`
- `USE_MIXED_PRECISION`
- `MAX_CACHE_IMAGE`
- `NG_IMAGE_SAVE`
- `PCA_VARIANCE`
- `ENABLE_AUGMENT`
- `CPU_OPTIMIZATION`
