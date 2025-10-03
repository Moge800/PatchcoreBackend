# テストスクリプト

## 概要
このディレクトリには、PatchCoreバックエンドの動作確認用テストスクリプトが含まれています。

## テストファイル

### gpu_check.py
GPU環境の確認とパフォーマンステスト
```bash
python tests/gpu_check.py
```

### benchmark_test.py
推論性能のベンチマークテスト（APIサーバー起動必須）
```bash
# 別ターミナルでサーバー起動
python src/api/run_api.py

# ベンチマーク実行
python tests/benchmark_test.py
```

### api_test.py
API基本動作確認と可視化テスト（APIサーバー起動必須）
```bash
# 別ターミナルでサーバー起動
python src/api/run_api.py

# テスト実行
python tests/api_test.py
```

## 実行順序

1. GPU環境確認
   ```bash
   python tests/gpu_check.py
   ```

2. APIサーバー起動
   ```bash
   python src/api/run_api.py
   ```

3. ベンチマークまたはAPI動作確認
   ```bash
   python tests/benchmark_test.py
   # または
   python tests/api_test.py
   ```