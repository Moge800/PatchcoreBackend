# 設定ファイルの役割分担ガイド

## 概要
PatchCoreBackendでは、設定を**環境変数（.env）**と**モデル設定（settings.py）**の2つに分けて管理しています。

## 設定の分類

### 📁 settings.py（モデル固有設定）
**モデルの学習・異常検出の本質に関わる設定**

#### 必ず設定が必要な項目
- `AFFINE_POINTS`: 射影変換の4点座標（GUIで設定）
- `IMAGE_SIZE`: 入力画像サイズ（モデル設計）
- `Z_SCORE_THRESHOLD`: 異常判定のZスコアしきい値
- `Z_AREA_THRESHOLD`: 異常ピクセル数しきい値
- `Z_MAX_THRESHOLD`: Zスコア最大値しきい値
- `FEATURE_DEPTH`: モデルレイヤー深度（1〜4）
- `PCA_VARIANCE`: PCA分散保持率（異常検出精度に影響）
- `ENABLE_AUGMENT`: データ拡張の有効化（学習時）
- `SAVE_FORMAT`: メモリバンク保存形式（compressed/full）

#### オプション項目（環境変数でオーバーライド可能）
- `USE_GPU`: GPU使用設定（.envで上書き可能）
- `GPU_DEVICE_ID`: GPUデバイスID（.envで上書き可能）
- `USE_MIXED_PRECISION`: 混合精度演算（.envで上書き可能）
- `NG_IMAGE_SAVE`: NG画像保存（.envで上書き可能）
- `MAX_CACHE_IMAGE`: キャッシュ画像数（.envで上書き可能）
- `CPU_OPTIMIZATION`: CPU最適化設定（.envで上書き可能）

### 🌍 .env（環境変数）
**実行環境に依存する設定**

#### アプリケーション設定
- `APP_NAME`: アプリケーション名
- `APP_VERSION`: バージョン
- `DEBUG`: デバッグモード

#### APIサーバー設定
- `API_HOST`: APIホスト
- `API_PORT`: APIポート
- `API_RELOAD`: 自動リロード
- `API_WORKERS`: ワーカー数

#### モデル設定
- `DEFAULT_MODEL_NAME`: デフォルトモデル名

#### ログ設定
- `LOG_LEVEL`: ログレベル（INFO, DEBUG等）
- `LOG_DIR`: ログディレクトリ

#### GPU設定（settings.pyをオーバーライド）
- `USE_GPU`: GPU使用（True/False）
- `GPU_DEVICE_ID`: GPUデバイスID（0, 1, 2...）
- `USE_MIXED_PRECISION`: 混合精度演算（True/False）

#### CPU最適化設定
- `CPU_THREADS`: CPUスレッド数
- `CPU_MEMORY_EFFICIENT`: メモリ効率重視

#### データ設定
- `DATA_DIR`: データセットディレクトリ
- `MODEL_DIR`: モデルディレクトリ
- `SETTINGS_DIR`: 設定ファイルディレクトリ

#### キャッシュ設定（settings.pyをオーバーライド）
- `MAX_CACHE_IMAGES`: 最大キャッシュ画像数
- `CACHE_TTL`: キャッシュTTL
- `NG_IMAGE_SAVE`: NG画像保存（True/False）

#### セキュリティ設定
- `API_KEY`: APIキー
- `ALLOWED_ORIGINS`: 許可オリジン

## 優先順位

設定の優先順位は以下の通りです：

```
1. .envファイルの環境変数（最優先）
   ↓
2. settings.pyの設定値
   ↓
3. デフォルト値
```

### 例：GPU設定の優先順位

```python
# settings.py で定義
USE_GPU = False

# .env で上書き
USE_GPU=True  # <- これが優先される

# 実際に使用される値: True
```

## GUI設定との関係

### GUIで変更可能な設定
GUI（`model_create_gui.py`）では以下の設定を変更できます：

1. **モデル選択**: `main_settings.py`の`MODEL_NAME`を変更
2. **アフィン座標取得**: `settings.py`の`AFFINE_POINTS`を更新
3. **設定ファイル編集**: `settings.py`を直接編集

### GUIで変更できない設定
以下の設定は`.env`ファイルを編集する必要があります：
- GPU設定
- ログレベル
- キャッシュサイズ
- APIサーバー設定

## 設定変更時の注意事項

### settings.pyの変更
- **学習前**: 自由に変更可能
- **学習後**: 以下の設定を変更すると再学習が必要
  - `IMAGE_SIZE`
  - `FEATURE_DEPTH`
  - `PCA_VARIANCE`
  - `ENABLE_AUGMENT`

### .envの変更
- アプリケーション再起動で即座に反映
- APIサーバーは`/restart_engine?execute=true`で再起動可能

## 推奨される使用方法

### 開発環境
```bash
# .env
DEBUG=True
LOG_LEVEL=DEBUG
USE_GPU=True
GPU_DEVICE_ID=0
MAX_CACHE_IMAGES=100
```

### 本番環境
```bash
# .env
DEBUG=False
LOG_LEVEL=INFO
USE_GPU=True
GPU_DEVICE_ID=0
MAX_CACHE_IMAGES=2000
API_KEY=<secure-key>
```

### モデル調整時
```python
# settings.py
Z_SCORE_THRESHOLD = 5.0  # より厳しく
Z_AREA_THRESHOLD = 50    # より許容的に
FEATURE_DEPTH = 2        # 精度向上
PCA_VARIANCE = 0.98      # 情報保持率向上
```

## 設定検証

### 設定ファイルの検証
```bash
python tests/validate_settings.py
```

検証対象：
- ✅ AFFINE_POINTS: 4点のリスト
- ✅ IMAGE_SIZE: (width, height)タプル
- ✅ しきい値: 正の数値
- ✅ PCA_VARIANCE: 0 < x <= 1
- ✅ FEATURE_DEPTH: 1, 2, 3, 4のいずれか
- ✅ SAVE_FORMAT: "compressed" or "full"
- ✅ ENABLE_AUGMENT: True or False

### GUI設定検証
GUI上の「設定検証」ボタンで以下を確認：
- 必須設定の存在
- データ型の正当性
- 値の範囲チェック

## トラブルシューティング

### 設定が反映されない
1. `.env`ファイルがプロジェクトルートにあるか確認
2. アプリケーションを再起動
3. `python -c "from src.config import env_loader; env_loader.print_config()"`で確認

### 設定検証エラー
```bash
# 詳細を確認
python tests/validate_settings.py

# GUIで確認
# 「設定検証」ボタンをクリック
```

### GPU設定が効かない
```bash
# 環境変数を確認
python -c "from src.config import env_loader; print(env_loader.USE_GPU)"

# settings.pyでの設定を確認
python -c "from src.config.settings_loader import SettingsLoader; loader = SettingsLoader('settings/models/example_model/settings.py'); print(loader.get_variable('USE_GPU'))"
```

## まとめ

### settings.pyで管理すべき設定
- ✅ モデル設計に関わる設定
- ✅ 異常検出アルゴリズムのパラメータ
- ✅ 学習時の設定
- ✅ GUIで変更する設定

### .envで管理すべき設定
- ✅ 実行環境依存の設定
- ✅ 開発/本番で異なる設定
- ✅ セキュリティ情報
- ✅ GPU/CPU切り替え
- ✅ ログレベル
