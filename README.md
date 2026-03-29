# PatchCore Backend

異常検知システムのバックエンド実装。PatchCoreアルゴリズムを使用した画像ベースの異常検知APIとGUIを提供します。

## 🚀 特徴

- **高速推論**: CPU環境で平均35ms、約30枚/秒のスループット
- **GPU対応**: CUDA環境でのGPUアクセラレーション対応
- **柔軟な設定**: モデル設定（settings.py）と環境設定（.env）の分離管理
- **REST API**: FastAPIによる高速かつ型安全なAPI
- **GUI**: 使いやすい学習・推論実行インターフェース
- **画像キャッシュ**: 推論結果の一時保存機能
- **設定検証**: GUI/CLIによる設定ファイルの妥当性チェック
- **統一ログ**: 環境変数で制御可能なロギングシステム

## 📋 システム要件

- Python 3.10以上
- Windows 11 / Linux
- （オプション）NVIDIA GPU + CUDA 12.4

## 🔧 インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/Moge800/PatchcoreBackend.git
cd PatchcoreBackend
```

### 2. 仮想環境の作成

```powershell
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 3. 依存関係のインストール

**CPU版（推奨）:**
```bash
pip install -r requirements-cpu.txt
```

**GPU版（CUDA 12.4）:**
```bash
pip install -r requirements-gpu.txt
```

### 4. 環境変数の設定

```powershell
# .envファイルを作成（初回のみ）
Copy-Item .env.example .env

# 必要に応じて.envファイルを編集
# USE_GPU=True  # GPU使用する場合
# LOG_LEVEL=DEBUG  # デバッグログを有効化
```

詳細は [環境変数ガイド](docs/ENV_GUIDE.md) と [設定ガイド](docs/SETTINGS_GUIDE.md) を参照してください。

## 📖 ドキュメント

全ドキュメントの一覧は [docs/INDEX.md](docs/INDEX.md) を参照してください。

| ドキュメント | 概要 |
|---|---|
| [サーバーガイド](docs/SERVER_GUIDE.md) | 起動・停止・推論フロー・トラブルシューティング |
| [GUI ガイド](docs/GUI_GUIDE.md) | GUI の操作方法 |
| [API リファレンス](docs/API.md) | REST API エンドポイント仕様 |
| [設定ガイド](docs/SETTINGS_GUIDE.md) | settings.py と .env の役割分担 |
| [環境変数ガイド](docs/ENV_GUIDE.md) | 全環境変数リファレンス |
| [セキュリティ](docs/SECURITY.md) | 本番環境向け推奨事項 |

## 📂 プロジェクト構造

```
PatchcoreBackend/
├── src/
│   ├── api/              # REST API
│   │   ├── core/         # API実装
│   │   ├── routers/      # エンドポイントルーター
│   │   ├── services/     # サービス層
│   │   ├── client/       # APIクライアント
│   │   └── utils/        # APIユーティリティ
│   ├── ml_engines/       # 機械学習エンジン
│   │   ├── PatchCore/    # PatchCore実装
│   │   └── U-Net/        # U-Net（将来拡張用）
│   ├── ui/               # GUI
│   ├── config/           # 設定管理
│   └── utils/            # 共通ユーティリティ
├── scripts/              # 起動・診断スクリプト
├── tests/                # テストスクリプト
├── datasets/             # 学習データ
├── models/               # 保存済みモデル
├── settings/             # 設定ファイル
│   └── models/           # モデル別設定
└── docs/                 # ドキュメント
```

## 🎯 クイックスタート

### 1. モデルの学習

```bash
# GUIから実行
python main_gui_launch.py

# またはコマンドラインから
python src/ml_engines/PatchCore/pipeline/create.py
```

### 2. APIサーバーの起動

```bash
# スクリプトで起動（推奨）
.\scripts\server_launch.ps1

# または直接起動
uvicorn src.api.core.patchcore_api:app --host 0.0.0.0 --port 8000
```

### 3. 推論の実行

**Python APIクライアント:**

```python
from src.api.client.patchcore_api_client import PatchCoreApiClient
import cv2

client = PatchCoreApiClient()
client.wait_for_server()

# モデルをロード（起動時自動ロード設定がない場合）
client.load_model("example_model")

# 推論（ジョブ投入→ポーリング→結果取得を内包）
image = cv2.imread("test.png")
result = client.predict("example_model", image)

print(f"判定: {result['label']}")  # OK or NG
print(f"統計: {result['z_stats']}")
```

**curl:**

```bash
# 1. モデルをロード
curl -X POST http://localhost:8000/models/example_model/load

# 2. 推論ジョブを投入（job_id が返る）
curl -X POST "http://localhost:8000/models/example_model/predict?detail_level=basic" \
  -F "file=@test.png"

# 3. 結果をポーリング（status が completed になるまで繰り返す）
curl http://localhost:8000/jobs/{job_id}
```

## 🔧 設定

### モデル設定ファイル

`settings/models/{model_name}/settings.py`:

```python
# 画像処理設定
AFFINE_POINTS = [[152, 96], [422, 98], [494, 361], [33, 352]]
IMAGE_SIZE = (224, 224)

# 異常検知しきい値
Z_SCORE_THRESHOLD = 4.5
Z_AREA_THRESHOLD = 100
Z_MAX_THRESHOLD = 10.0

# GPU設定
USE_GPU = True
GPU_DEVICE_ID = 0
USE_MIXED_PRECISION = True

# モデル設定
FEATURE_DEPTH = 1
PCA_VARIANCE = 0.95
SAVE_FORMAT = "compressed"
```

## 📊 API エンドポイント

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/models` | モデル一覧 |
| GET | `/models/{name}/status` | モデルステータス |
| POST | `/models/{name}/load` | モデルをロード |
| DELETE | `/models/{name}/unload` | モデルをアンロード |
| DELETE | `/models/{name}` | モデルを完全削除 |
| POST | `/models/{name}/predict` | 推論ジョブ投入 |
| GET | `/jobs/{job_id}` | ジョブ状態・結果取得 |
| GET | `/jobs` | ジョブ一覧 |
| GET | `/models/{name}/images` | 画像ID一覧 |
| GET | `/models/{name}/images/{id}` | キャッシュ画像取得（PNG） |
| POST | `/models/{name}/images/clear` | 画像キャッシュクリア |
| GET | `/system_info` | システム情報取得 |
| GET | `/gpu_info` | GPU情報取得 |

## 🧪 テスト

```bash
# GPU環境チェック
python tests/gpu_check.py

# ベンチマークテスト
python tests/benchmark_test.py

# API動作確認（可視化付き）
python tests/api_test.py
```

## 📈 パフォーマンス

**CPU環境（Intel Core i7-12700）:**
- 平均処理時間: 35ms
- スループット: 28.9枚/秒
- 標準偏差: 3ms

**GPU環境（RTX 3090）:**
- 小規模バッチ（N=1）ではCPUと同等
- 大規模バッチで高速化が期待できる

## 🐛 トラブルシューティング

### CUDAが認識されない

```bash
# CUDA確認
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# GPU版PyTorch再インストール
pip install -r requirements-gpu.txt --force-reinstall
```

### メモリ不足エラー

設定ファイルで以下を調整:
- `IMAGE_SIZE` を小さくする
- `FEATURE_DEPTH` を減らす
- `USE_GPU = False` に変更

## 🤝 コントリビューション

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 👥 開発者

- Moge800

## 📞 サポート

問題が発生した場合は、GitHubのIssueセクションで報告してください。
