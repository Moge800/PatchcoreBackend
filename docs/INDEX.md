# ドキュメント一覧

PatchCore Backend のドキュメントガイドです。目的に応じて適切なドキュメントを参照してください。

## 🗺️ ドキュメントマップ

```
初めての方 → SERVER_GUIDE.md → API.md
設定を変更したい → SETTINGS_GUIDE.md → ENV_GUIDE.md
GUIを使いたい → GUI_GUIDE.md
本番環境に出す → SECURITY.md → API_SETTINGS.md
```

## 📖 ドキュメント一覧

### 運用ガイド

| ドキュメント | 概要 | 対象読者 |
|---|---|---|
| [SERVER_GUIDE.md](SERVER_GUIDE.md) | サーバーの起動・停止、推論フロー、トラブルシューティング | 全ユーザー |
| [GUI_GUIDE.md](GUI_GUIDE.md) | GUI の操作方法、設定検証機能の使い方 | GUI ユーザー |

### 設定・環境

| ドキュメント | 概要 | 対象読者 |
|---|---|---|
| [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md) | settings.py と .env の役割分担、優先順位、設定項目一覧 | 全ユーザー |
| [ENV_GUIDE.md](ENV_GUIDE.md) | .env ファイルの全環境変数リファレンス、使用シナリオ別設定例 | 設定を詳細に調整したい方 |
| [API_SETTINGS.md](API_SETTINGS.md) | サーバー/クライアントの接続設定（HOST/PORT）の分離仕様 | リモート接続・LAN 運用する方 |

### API 仕様

| ドキュメント | 概要 | 対象読者 |
|---|---|---|
| [API.md](API.md) | REST API 全エンドポイントの仕様、リクエスト/レスポンス形式 | API 開発者 |

### セキュリティ・本番運用

| ドキュメント | 概要 | 対象読者 |
|---|---|---|
| [SECURITY.md](SECURITY.md) | 本番環境向けセキュリティ推奨事項、チェックリスト | 本番デプロイ担当者 |

### 開発・設計ドキュメント

| ドキュメント | 概要 | 状態 |
|---|---|---|
| [VALIDATION_FEATURE.md](VALIDATION_FEATURE.md) | 設定検証機能の実装レポート | ✅ 実装済み |
| [GUI_ENHANCEMENT_PROPOSAL.md](GUI_ENHANCEMENT_PROPOSAL.md) | GUI 機能拡張の提案書（Phase 1〜3） | 📝 提案段階（Phase 1 一部実装済み） |

## 🔗 設定関連ドキュメントの使い分け

設定に関するドキュメントが複数あるため、用途に応じて参照してください。

- **設定の全体像を知りたい** → [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md)
- **環境変数の一覧・詳細を確認したい** → [ENV_GUIDE.md](ENV_GUIDE.md)
- **リモート接続の HOST/PORT を設定したい** → [API_SETTINGS.md](API_SETTINGS.md)

## 📂 スクリプト一覧

`scripts/` ディレクトリの補助スクリプトです。

| スクリプト | 用途 |
|---|---|
| `server_launch.ps1` | API サーバー起動（Windows） |
| `server_launch.sh` | API サーバー起動（Linux/Mac） |
| `launch_settings_gui.ps1` | 設定用 GUI 起動 |
| `restart_engine.ps1` | 推論エンジン再起動（API 経由） |
| `benchmark.ps1` | ベンチマークテスト実行 |
| `test_gui.ps1` | GUI 実行環境の事前チェック |
| `test_paths.ps1` | パス・依存関係の存在確認 |
