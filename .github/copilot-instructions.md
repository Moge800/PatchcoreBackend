# GitHub Copilot Instructions

## プロジェクト概要
PatchCoreアルゴリズムを使用した異常検知システムのバックエンド実装。FastAPIによるREST API、Tkinter GUI、CPU/GPU両対応の推論エンジンを提供し、画像ベースの異常検知を高速に実行する。

## 技術スタック
- **Python**: 3.10以上
- **パッケージマネージャ**: uv (requirements.txtも併用)
- **Webフレームワーク**: FastAPI 0.118.2, Uvicorn
- **機械学習**: PyTorch 2.8.0, torchvision, scikit-learn
- **画像処理**: OpenCV, Pillow
- **GUI**: Tkinter (標準ライブラリ)
- **データ検証**: Pydantic 2.x
- **環境変数**: python-dotenv
- **開発ツール**: mypy, Black, Ruff, pytest

## プロジェクト構造
```
PatchcoreBackend/
├── src/
│   ├── api/              # REST API
│   │   ├── core/         # patchcore_api.py (FastAPI実装)
│   │   ├── client/       # APIクライアント
│   │   └── utils/        # APIユーティリティ
│   ├── ml_engines/       # 機械学習エンジン
│   │   └── PatchCore/    # PatchCore実装
│   │       ├── core/     # inference_engine.py, inference_core.py
│   │       ├── pipeline/ # create.py (学習), inference.py
│   │       └── utils/    # モデルローダー、デバイス管理等
│   ├── ui/               # GUI (Tkinter)
│   │   ├── main_gui_launcher.py
│   │   ├── settings_gui_editor.py
│   │   ├── env_gui_editor.py
│   │   └── projection_point_selector.py
│   ├── config/           # 設定管理
│   │   ├── env_loader.py      # .env読み込み
│   │   ├── settings_loader.py # settings.py読み込み
│   │   └── constants.py       # パス定数 (2025-12-03追加)
│   ├── utils/            # 共通ユーティリティ
│   │   └── logger.py     # 統一ロガー
│   └── types.py          # TypedDict定義
├── settings/             # モデル別設定
│   └── models/
│       └── <model_name>/
│           └── settings.py  # モデル固有設定
├── models/               # 保存済みモデル
├── datasets/             # 学習データ
├── tests/                # テストスクリプト
├── docs/                 # ドキュメント
└── scripts/              # PowerShellスクリプト
```

**アーキテクチャ設計**:
- **シングルトンパターン**: `PatchCoreInferenceEngine`はモデルごとに1インスタンス
- **設定の階層化**: 環境設定(`.env`) + モデル設定(`settings.py`)
- **型安全性**: TypedDict、Pydantic、型ヒント必須
- **モジュール分離**: API層、推論層、UI層を明確に分離

## コーディング規約

### 1. 型ヒントは必須
```python
# Good
def predict(self, image: np.ndarray) -> PredictionResult:
    return PredictionResult(label="OK", ...)

# Bad
def predict(self, image):
    return {"label": "OK"}
```

**重要**: 戻り値の型ヒントも必ず記述

### 2. 環境変数の扱い
- **`.env`ファイルは必須** (`.env.example`をコピー)
- `src/config/env_loader.py`で型安全に管理
- 設定のオーバーライド優先順位:
  1. `.env` (環境変数)
  2. `settings.py` (モデル設定)
  3. デフォルト値

```python
# Good
from src.config import env_loader
model_name = env_loader.DEFAULT_MODEL_NAME

# Bad
import os
model_name = os.getenv("DEFAULT_MODEL_NAME")
```

### 3. パス管理
**2025-12-03追加**: `src/config/constants.py`を使用してパスを中央管理

```python
# Good
from src.config.constants import get_model_dir, get_settings_path
model_dir = get_model_dir(model_name)
settings_path = get_settings_path(model_name)

# Bad
model_dir = os.path.join("models", model_name)
settings_path = os.path.join("settings", "models", model_name, "settings.py")
```

### 4. エラーハンドリング
- **`Exception`の汎用捕捉は最小限に**
- 具体的な例外を指定: `FileNotFoundError`, `ValueError`, `RuntimeError`など
- API層では`JSONResponse`でエラーを返す

```python
# Good
try:
    model = load_model(path)
except FileNotFoundError as e:
    logger.error(f"Model not found: {e}")
    raise RuntimeError(f"Failed to load model: {e}")

# Bad
try:
    model = load_model(path)
except Exception as e:
    pass
```

### 5. マジックナンバーは定数化
```python
# Good (settings.pyまたはconstants.py)
Z_SCORE_THRESHOLD = 4.5
Z_AREA_THRESHOLD = 100

# Bad
if z_score > 4.5 and area > 100:
    label = "NG"
```

### 6. グローバル変数の扱い
- **シングルトン以外でのグローバル変数は避ける**
- API層の`engine`は例外的にモジュールレベルで定義
- `global`キーワードは最小限に

```python
# Good (シングルトン)
class PatchCoreInferenceEngine:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Bad
global_config = {}  # グローバル辞書
```

### 7. インポート順序
```python
# 標準ライブラリ
import os
from typing import Optional, Dict
from pathlib import Path

# サードパーティ
import numpy as np
import cv2
import torch
from fastapi import FastAPI
from pydantic import BaseModel

# ローカル
from src.types import PredictionResult
from src.config import env_loader
from src.config.constants import get_model_dir
from src.utils.logger import setup_logger
```

### 8. ロギング
- **`src.utils.logger.setup_logger()`を使用**
- ログレベル: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `.env`の`LOG_LEVEL`で制御
- ファイルとコンソール両方に出力

```python
from src.utils.logger import setup_logger

logger = setup_logger("module_name", log_dir="logs/inference")
logger.info("Model loaded successfully")
logger.error(f"Prediction failed: {e}", exc_info=True)
```

### 9. GPU/CPU対応
- **`src/ml_engines/PatchCore/utils/device_utils.py`を使用**
- 環境変数`USE_GPU`で切り替え
- 混合精度計算サポート

```python
from src.ml_engines.PatchCore.utils.device_utils import get_device, clear_gpu_cache

device = get_device(use_gpu=True, device_id=0)
model = model.to(device)

# 処理後
clear_gpu_cache()
```

### 10. type: ignoreは最小限に
- 型を正しく定義すれば不要なはず
- やむを得ない場合のみ使用し、理由をコメント

```python
# Good (型を正しく定義)
def get_stats() -> Dict[str, float]:
    return {"mean": 0.5, "std": 0.2}

# Bad
def get_stats():  # type: ignore
    return {"mean": 0.5, "std": 0.2}
```

### 11. ファイルエンコーディング
- **PowerShellスクリプト (`.ps1`)**: UTF-8 BOM付き
- **その他すべて**: UTF-8 BOMなし
  - Python (`.py`)
  - Markdown (`.md`)
  - JSON (`.json`)
  - 設定ファイル (`.env`)

**理由**: PowerShellは歴史的経緯でBOMなしUTF-8を正しく解釈できない場合がある

## PatchCore推論エンジンの注意点

### シングルトンパターン
- `PatchCoreInferenceEngine`はモデルごとに1インスタンス
- `_instance`クラス属性で管理
- 再初期化時は`PatchCoreInferenceEngine._instance = None`

### 画像キャッシュ
- `image_store`に推論結果画像を保存
- `MAX_CACHE_IMAGES`で上限設定
- `OrderedDict`でLRU管理

### 非同期NG画像保存
- NG判定時にスレッドで画像保存
- `NG_IMAGE_SAVE=True`で有効化
- `datasets/<model_name>/output/NG/`に保存

### GPU最適化
- 混合精度計算 (`torch.amp.autocast`)
- デバイス間のテンソル移動に注意
- モデル保存時はCPUに移動してからトレース

## FastAPI特有の考慮事項

### デコレータパターン
```python
@engine_required
async def predict(...) -> JSONResponse:
    # engineが初期化済みか自動チェック
```

### クエリパラメータ
```python
# Good (型ヒント + バリデーション)
limit: int = Query(100, ge=1, le=1000)
prefix: str | None = Query(None, enum=["org", "ovr"])

# Bad
limit = request.args.get("limit")
```

### レスポンス
- 常に`JSONResponse`を返す
- ステータスコードを明示
- `detail_level`パラメータで応答の詳細度制御

## Tkinter GUIの考慮事項

### スレッド処理
- **長時間処理は`threading.Thread`で実行**
- GUI更新は`after()`メソッド使用
- プロセス管理は`subprocess.Popen`

### 設定エディタ
- `SettingsGUIEditor`: モデル設定編集
- `EnvGUIEditor`: 環境変数編集
- バリデーション後に保存

### プロジェクションポイント選択
- `ProjectionPointSelector`: アフィン変換座標選択
- OpenCVで画像表示、マウスクリックで座標取得

## セキュリティ

### 環境変数
- `.env`はGitにコミットしない (`.gitignore`済み)
- モデル名、デバイスID等は環境変数化
- APIキーや認証情報は将来的に追加検討

### ログファイル
- `logs/`, `log/`は`.gitignore`で除外
- 機密情報をログに出力しない
- `DEBUG`モード時のみ詳細ログ

### API認証
- **現状: 認証機構なし** (ローカル使用想定)
- 本番環境では認証追加を検討
- CORS設定は必要に応じて追加

## テスト

### テスト構造
```
tests/
├── api_test.py           # API動作確認
├── benchmark_test.py     # 性能計測
├── gpu_check.py          # GPU環境確認
├── predict_test.py       # 推論テスト
├── test_settings_loader.py
└── validate_settings.py  # 設定検証
```

### テスト駆動開発(TDD)の推奨
**新機能追加時は必ずテストも同時作成する**

#### テスト作成ルール
1. **新しい推論機能** → 対応するテストを`tests/`に作成
2. **API変更** → `api_test.py`を更新
3. **設定変更** → バリデーションテスト追加

#### テスト実行コマンド
```bash
# 全テスト実行
pytest tests/ -v

# 特定のテスト
pytest tests/api_test.py -v

# カバレッジ計測
pytest --cov=src tests/
```

#### モックの使用
```python
from unittest.mock import MagicMock, patch

@patch("src.ml_engines.PatchCore.core.inference_engine.load_model_and_assets")
def test_engine_init(mock_load):
    mock_load.return_value = (model, memory_bank, pca, mean, std)
    engine = PatchCoreInferenceEngine("test_model")
    assert engine.model_name == "test_model"
```

## デプロイ

### 依存関係インストール
```powershell
# CPU版
pip install -r requirements-cpu.txt

# GPU版 (CUDA 12.4)
pip install -r requirements-gpu.txt

# uvを使う場合
uv sync
```

### 起動方法
```powershell
# APIサーバー起動
python -m uvicorn src.api.core.patchcore_api:app --host 0.0.0.0 --port 8000

# またはスクリプト使用
.\scripts\server_launch.ps1

# GUI起動
python main_gui_launch.py
```

### 環境確認
```python
# GPU利用可能か確認
python tests/gpu_check.py

# 設定ファイル検証
python tests/validate_settings.py settings/models/<model_name>/settings.py
```

## よくある問題と解決策

### インポートエラー
- プロジェクトルートから実行 (`python -m src.api.core.patchcore_api`)
- 絶対インポート使用 (`from src.config import env_loader`)
- `sys.path.insert(0, ".")`は最小限に

### .envが見つからない
- `.env.example`を`.env`にコピー
- `DEFAULT_MODEL_NAME`等の必須変数を設定
- `env_loader.py`でパスを確認

### モデルが読み込めない
- `models/<model_name>/`に以下が存在するか確認:
  - `model.pt`
  - `memory_bank.pkl` または `memory_bank_compressed.pkl`
  - `pca.pkl`
  - `pixel_stats.pkl`
- `SAVE_FORMAT`設定を確認

### GPU関連エラー
- `USE_GPU=False`でCPUモード確認
- CUDA互換性確認 (`torch.cuda.is_available()`)
- GPU_DEVICE_ID設定確認

### 推論結果がおかしい
- `Z_SCORE_THRESHOLD`, `Z_AREA_THRESHOLD`を調整
- 学習データの質を確認
- `AFFINE_POINTS`で入力画像の歪み補正確認

## コード品質

### 静的解析ツール
- **mypy**: 型チェック (`pyproject.toml`で設定済み)
- **Black**: コードフォーマッター (line-length: 88)
- **Ruff**: 高速linter

### 実行コマンド
```powershell
# 型チェック
mypy src/ --ignore-missing-imports

# フォーマット
black src/ tests/

# Lint
ruff check src/ tests/
```

### VSCode設定
- `.vscode/settings.json`で自動フォーマット設定
- Pylanceで型チェック
- 保存時に自動整形

## 命名規則

### Python
- **クラス**: `PascalCase` (`PatchCoreInferenceEngine`, `SettingsLoader`)
- **関数/変数**: `snake_case` (`predict`, `z_score_map`, `image_id`)
- **定数**: `UPPER_SNAKE_CASE` (`Z_SCORE_THRESHOLD`, `MAX_CACHE_IMAGES`)
- **プライベート**: `_leading_underscore` (`_instance`, `_warmup`)
- **モジュール**: `snake_case` (`inference_engine.py`, `device_utils.py`)

### ディレクトリ/ファイル
- **モジュール名**: `snake_case` (例: `ml_engines`, `patchcore_api.py`)
- **設定ディレクトリ**: `models/<model_name>/`
- **ログディレクトリ**: `logs/<module>/`

## ドキュメント

### Docstring
- **スタイル**: Google Style
- **必須箇所**: すべてのpublic関数・クラス
- **含める内容**: 引数、戻り値、例外、使用例

```python
def predict(self, image: np.ndarray) -> PredictionResult:
    """
    画像の異常検出を実行

    Args:
        image: 入力画像 (BGR形式, np.ndarray)

    Returns:
        PredictionResult: 予測結果
            - label: "OK" または "NG"
            - z_stats: Z-score統計情報
            - thresholds: しきい値情報

    Raises:
        ValueError: 画像サイズが不正な場合
        RuntimeError: 推論エラー時

    Example:
        >>> engine = PatchCoreInferenceEngine("model_name")
        >>> result = engine.predict(image)
        >>> print(result["label"])
        "OK"
    """
```

### コメント
- **複雑なロジック**: インラインコメントで説明
- **TODOコメント**: `# TODO: <内容>`形式
- **ハックや回避策**: 理由を明記

## 定期メンテナンス手順

### 大きな変更時・仕事終わりのチェックリスト

#### 1. 全スキャンによるテスト項目チェック
```bash
# 主要モジュールをスキャン
semantic_search "inference prediction API endpoints"

# 既存テストと比較して未カバーを特定
```

**チェック対象**:
- [ ] 新規追加した推論機能にテストがあるか
- [ ] API変更のテストケースが十分か
- [ ] 設定変更のバリデーションテストがあるか
- [ ] エラーハンドリングのテストが網羅されているか

#### 2. 開発ログの作成
`dev_logs/YYYY-MM-DD.md`形式でその日の開発内容を記録:

```markdown
# 開発ログ - YYYY-MM-DD

## 📋 実施内容サマリー
...

## 🧪 テスト実行結果
...

## 📊 パフォーマンス計測
- 推論速度: XX ms/枚
- GPU使用率: XX%
- メモリ使用量: XX MB

## 🔍 発見した課題と対応
...

## 📌 まとめ
...
```

#### 3. コミット前の最終チェック
```powershell
# 1. 全テスト実行
pytest tests/ -v

# 2. 型チェック
mypy src/ --ignore-missing-imports

# 3. Lint
ruff check src/ tests/

# 4. フォーマット確認
black --check src/ tests/

# 5. 変更差分確認
git status
git diff

# 6. コミット
git add .
git commit -m "feat: <変更内容の要約>"
git push origin main
```

### 推奨頻度
- **テストチェック**: 大きな機能追加時 or 1日の終わり
- **開発ログ作成**: 1日の終わり
- **パフォーマンス計測**: モデル変更時 or 週1回
- **依存関係更新**: 月1回

### メリット
- 推論精度・速度の変化を追跡
- モデル改善の履歴が残る
- バグの早期発見
- ドキュメントとしても活用可能

## プロジェクト固有の重要事項

### モデルファイル構成
```
models/<model_name>/
├── model.pt                    # TorchScript形式モデル
├── memory_bank.pkl             # 非圧縮メモリバンク
├── memory_bank_compressed.pkl  # PCA圧縮済み (推奨)
├── pca.pkl                     # PCA変換器
└── pixel_stats.pkl             # (pixel_mean, pixel_std)
```

### 設定ファイル構成
```
settings/models/<model_name>/
└── settings.py                 # モデル固有設定
    - IMAGE_SIZE
    - AFFINE_POINTS
    - Z_SCORE_THRESHOLD
    - FEATURE_DEPTH
    - PCA_VARIANCE
    など
```

### ベンチマーク
- CPU推論: 平均35ms/枚 (約30枚/秒)
- GPU推論: 環境依存 (混合精度で高速化)
- メモリ使用量: モデルサイズに依存

### 推奨ワークフロー
1. **データ準備**: `datasets/<model_name>/normal/`に正常画像配置
2. **学習実行**: `python src/ml_engines/PatchCore/pipeline/create.py`
3. **設定調整**: GUIまたは直接`settings.py`編集
4. **推論テスト**: `python tests/predict_test.py`
5. **API起動**: `.\scripts\server_launch.ps1`
6. **本番運用**: クライアントから`/engine/predict`を呼び出し

---

**このプロジェクトは異常検知システムの学習・実験用です。質問や改善提案は歓迎します！**
