# 📄 setup_db.py 仕様書.

## 概要

- 初回セットアップ専用スクリプト。
- 実行すると以下を自動化する。

| 機能                   | 内容 |
|:------------------------|:-----|
| .env管理                 | 必要な MySQL / Supabase キーが不足していれば `.env` に追記 |
| requirements補完         | `requirements.txt` に不足パッケージを自動追記（重複回避） |
| ディレクトリ・ファイル作成 | `instance/`、`migrations/`、`app/models/` などを自動生成 |
| app/__init__.py更新       | `app/__init__.py` を安全に `.bak` へ退避後、絶対パス補正機能付きで上書き |
| 初期モデル作成            | `User` テーブル（id, name カラム）を作成 |
| 初期画面作成              | `/dbtest/` で DB 接続確認できるページ作成 |
| Flask-Migrate連携         | `flask db init` → `migrate` → `upgrade` を自動実行 |
| add_model.py生成         | モデル追加CLIを同時生成（生成済モデルの登録・マイグレーション付き）

## add_model.py（生成されるCLI）

- **目的**: 新しいモデルファイル（テーブル）を簡単に作成・即反映する
- **流れ**:
  1. `テーブル名` を入力
  2. カラム名・型を対話形式で追加（idは自動付与）
  3. `app/models/` に新しいモデルファイルを生成
  4. `app/models/__init__.py` にインポート文を追記
  5. `app/pages/dbtest/view.py` にインポート文を追記（存在する場合のみ）
  6. 自動で以下のコマンドを実行し、DBに即反映  
     ```
     flask db migrate -m "add <table> table"
     flask db upgrade
     ```

- **カラム型入力例**  
  String(255), Integer, Boolean, DateTime, Text, Float, JSON など

- **__repr__の生成形式**
  ```python
  return f'<Tablename {self.id}:{self.name}:{self.created_at}>'
  ```
  ※カラム名は自動的に `:` 区切りで並べられます

## 注意事項

- `add_model.py` 実行時にモデルを追加するだけで、マイグレーションまで自動で実行されます。
- モデルファイルは `models/__init__.py` と `dbtest/view.py` に自動インポートされるため、手動インポート不要です。
- すでに同名のテーブルファイルが存在する場合は上書きされません。
- `setup_db.py` 実行時、既存の `app/__init__.py` は `.bak` へ退避され、SQLite の相対パス問題も同時に解決されます。

## 最低動作環境

- Python 3.12以上
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- python-dotenv

## 使用例

### 1. 初期セットアップ

```bash
python setup_db.py
```

上記により以下が一括で実行されます：

- `.env` と `requirements.txt` 補完
- ディレクトリと初期ファイルの生成
- Flask-Migrate 初期化と `User` テーブルの作成

### 2. モデル追加（例：Postテーブルを追加）

```bash
python add_model.py
```

→ 以下が自動で行われます：

- モデル `Post` を作成
- 必要なファイルに import 追加
- `flask db migrate` & `flask db upgrade` 実行
