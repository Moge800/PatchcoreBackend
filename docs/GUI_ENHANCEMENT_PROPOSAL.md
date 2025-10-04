# GUI機能強化の提案

## 現状の問題点

現在のGUIは`settings.py`の編集と検証のみをサポートしており、`.env`ファイルの環境変数設定には対応していません。

## 提案する機能追加

### 1. 環境変数設定パネルの追加

#### 機能概要
- GUI上で`.env`ファイルの主要設定を変更可能にする
- 変更後は自動的に`.env`ファイルに保存
- リアルタイムで設定の反映状態を確認

#### 実装イメージ
```python
# 新しいタブまたはウィンドウ
[環境設定タブ]
┌─────────────────────────────────┐
│ GPU設定                          │
│ ☑ GPU使用 (USE_GPU)             │
│ GPUデバイスID: [0] ▼            │
│ ☑ 混合精度演算                   │
│                                 │
│ ログ設定                         │
│ ログレベル: [INFO] ▼            │
│ ログディレクトリ: [logs]        │
│                                 │
│ キャッシュ設定                   │
│ 最大キャッシュ画像数: [1200]    │
│ ☑ NG画像保存                     │
│                                 │
│ [保存] [デフォルトに戻す]       │
└─────────────────────────────────┘
```

### 2. 設定情報の統合表示

#### 現在の表示
```
基本設定:
  IMAGE_SIZE: (224, 224)
  FEATURE_DEPTH: 1
  SAVE_FORMAT: compressed
  USE_GPU: False
```

#### 改善後の表示
```
基本設定:
  IMAGE_SIZE: (224, 224) [settings.py]
  FEATURE_DEPTH: 1 [settings.py]
  SAVE_FORMAT: compressed [settings.py]
  
実行環境設定:
  USE_GPU: False [.env] ⚠️ settings.pyの値を上書き中
  GPU_DEVICE_ID: 0 [.env]
  LOG_LEVEL: INFO [.env]
  MAX_CACHE_IMAGES: 1200 [.env]
```

### 3. クイック設定切り替え

#### 機能概要
よく使う設定の組み合わせをプリセットとして保存

```python
[プリセット選択]
┌─────────────────────────────────┐
│ プリセット: [開発環境] ▼        │
│                                 │
│ 開発環境:                       │
│   - DEBUG=True                  │
│   - LOG_LEVEL=DEBUG             │
│   - USE_GPU=True                │
│                                 │
│ 本番環境:                       │
│   - DEBUG=False                 │
│   - LOG_LEVEL=INFO              │
│   - MAX_CACHE_IMAGES=2000       │
│                                 │
│ [適用] [新規作成]               │
└─────────────────────────────────┘
```

### 4. 設定の比較・差分表示

#### 機能概要
settings.pyと.envの設定の関係を可視化

```
[設定差分表示]
┌─────────────────────────────────────────────────┐
│ 設定項目      │ settings.py │ .env   │ 実際の値 │
├──────────────┼─────────────┼────────┼──────────┤
│ USE_GPU      │ False       │ True   │ True ⚠️ │
│ GPU_DEVICE   │ 0           │ 1      │ 1 ⚠️    │
│ MAX_CACHE    │ 1200        │ (未設定)│ 1200    │
│ LOG_LEVEL    │ (未設定)    │ DEBUG  │ DEBUG   │
└─────────────────────────────────────────────────┘

⚠️ = .envで上書きされています
```

### 5. 環境変数のリセット機能

```python
[環境変数管理]
┌─────────────────────────────────┐
│ 現在の状態:                      │
│ ☑ .envファイル存在              │
│ ☑ 6個の設定が上書き中           │
│                                 │
│ [.envファイルを削除]            │
│ → settings.pyの設定のみを使用   │
│                                 │
│ [.env.exampleから再作成]        │
│ → デフォルト設定に戻す          │
└─────────────────────────────────┘
```

## 実装の優先順位

### Phase 1: 最小限の機能（推奨）
1. **環境変数表示の追加**
   - 設定検証時に.envの値も表示
   - settings.pyとの差分を明示

### Phase 2: 基本的な編集機能
2. **簡易編集ダイアログ**
   - GPU設定のON/OFF切り替え
   - ログレベルの変更
   - キャッシュサイズの調整

### Phase 3: 高度な機能
3. **プリセット機能**
   - よく使う設定の保存・読み込み
4. **設定比較ビュー**
   - 差分の可視化

## 実装コード例（Phase 1）

### 設定検証時の表示強化

```python
def _on_validate_settings_click(self):
    """設定ファイルを検証"""
    settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
    self._log_message(f"\n[設定検証開始] {settings_path}\n")
    self._log_message("=" * 60 + "\n")

    try:
        loader = SettingsLoader(settings_path)
        self._log_message("✓ 設定ファイルの読み込み成功\n\n")

        # settings.py固有の設定
        self._log_message("モデル設定 (settings.py):\n")
        self._log_message(f"  IMAGE_SIZE: {loader.get_variable('IMAGE_SIZE')}\n")
        self._log_message(f"  FEATURE_DEPTH: {loader.get_variable('FEATURE_DEPTH')}\n")
        self._log_message(f"  PCA_VARIANCE: {loader.get_variable('PCA_VARIANCE')}\n")
        self._log_message(f"  ENABLE_AUGMENT: {loader.get_variable('ENABLE_AUGMENT')}\n\n")

        # 環境変数で上書き可能な設定
        self._log_message("実行環境設定 (.envで上書き可能):\n")
        
        # 環境変数の読み込み
        from src.config import env_loader
        
        use_gpu_settings = loader.module.USE_GPU
        use_gpu_actual = loader.get_variable('USE_GPU')
        if use_gpu_settings != use_gpu_actual:
            self._log_message(f"  USE_GPU: {use_gpu_actual} ⚠️ (.env={env_loader.USE_GPU}, settings.py={use_gpu_settings})\n")
        else:
            self._log_message(f"  USE_GPU: {use_gpu_actual}\n")
        
        self._log_message(f"  GPU_DEVICE_ID: {loader.get_variable('GPU_DEVICE_ID')}\n")
        self._log_message(f"  MAX_CACHE_IMAGE: {loader.get_variable('MAX_CACHE_IMAGE')}\n")
        self._log_message(f"  NG_IMAGE_SAVE: {loader.get_variable('NG_IMAGE_SAVE')}\n\n")
        
        # 環境変数のみの設定
        self._log_message("環境設定 (.envのみ):\n")
        self._log_message(f"  LOG_LEVEL: {env_loader.LOG_LEVEL}\n")
        self._log_message(f"  LOG_DIR: {env_loader.LOG_DIR}\n")
        self._log_message(f"  DEFAULT_MODEL_NAME: {env_loader.DEFAULT_MODEL_NAME}\n\n")

        # しきい値の表示
        self._log_message("異常検出しきい値:\n")
        self._log_message(f"  Z_SCORE_THRESHOLD: {loader.get_variable('Z_SCORE_THRESHOLD')}\n")
        self._log_message(f"  Z_AREA_THRESHOLD: {loader.get_variable('Z_AREA_THRESHOLD')}\n")
        self._log_message(f"  Z_MAX_THRESHOLD: {loader.get_variable('Z_MAX_THRESHOLD')}\n\n")

        # 詳細検証
        is_valid, errors = loader.validate_model_settings()

        self._log_message("=" * 60 + "\n")
        if is_valid:
            self._log_message("✓ 設定ファイルは正常です\n\n")
            messagebox.showinfo("検証成功", "設定ファイルは正常です")
        else:
            self._log_message("✗ 設定ファイルにエラーがあります:\n")
            for error in errors:
                self._log_message(f"  - {error}\n")
            self._log_message("\n")
            messagebox.showerror("検証失敗", f"設定ファイルにエラーがあります:\n\n" + "\n".join(errors))

    except FileNotFoundError as e:
        self._log_message(f"✗ エラー: {e}\n\n")
        messagebox.showerror("エラー", str(e))
    except Exception as e:
        self._log_message(f"✗ 予期しないエラー: {e}\n\n")
        import traceback
        self._log_message(traceback.format_exc())
        messagebox.showerror("エラー", f"予期しないエラー: {e}")
```

## メリット

### ユーザー視点
- ✅ コマンドラインなしで環境設定を変更可能
- ✅ 設定の関係性を視覚的に理解しやすい
- ✅ 開発/本番環境の切り替えが容易

### 開発者視点
- ✅ 設定ミスを減らせる
- ✅ トラブルシューティングが容易
- ✅ 環境変数システムの利用促進

## デメリット・注意点

1. **GUI実装の複雑化**
   - 環境変数の編集機能追加でコード量増加
   
2. **設定の二重管理**
   - GUIとファイル編集の両方で変更可能になり混乱の可能性

3. **.envファイルのフォーマット保持**
   - コメントや空行を保持したまま編集する必要がある

## 推奨する実装方針

**Phase 1の実装を推奨**します：
- まずは設定検証時に環境変数の状態も表示
- ファイル編集は従来通り手動で行う
- 設定の可視化に集中し、複雑な編集UIは後回し

これにより：
- 実装コストを抑えつつ
- ユーザーは設定の関係性を理解でき
- 必要に応じてPhase 2以降を検討できる
