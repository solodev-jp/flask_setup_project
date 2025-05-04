
# setup_project.py 仕様書

## 概要
Flaskプロジェクトを初期構築する自動化スクリプトです。  
Next.js風のディレクトリ構成（ページ単位のview.py＋index.html管理）を採用し、  
開発初期の手間を大幅に削減します。

## 主な機能
- プロジェクト基本構成の自動生成
- ページ単位のディレクトリ＋ファイル作成（view.py、index.html）
- templates、static(css/js)、layout.htmlの自動生成
- .env、.gitignoreの自動生成
- app直下でFlaskアプリをcreate_appパターンで構成
- ChoiceLoaderを使用し、app/pagesとapp/templates両方をテンプレート探索対象に設定
- ページ追加用CLI（add_page.py）も同時生成
- フォルダごとに__init__.pyを自動生成（モジュール管理対応）

## 生成されるディレクトリ構成

```
your_project/
├── run.py
├── setup_project.py
├── add_page.py
├── requirements.txt
├── .env
├── .gitignore
└── app/
    ├── __init__.py
    ├── common/
    │   ├── __init__.py
    │   ├── utils.py
    │   ├── filters.py
    │   └── globals.py
    ├── pages/
    │   ├── __init__.py
    │   └── index/
    │       ├── __init__.py
    │       ├── view.py
    │       └── index.html
    ├── templates/
    │   └── layout.html
    └── static/
        ├── css/
        │   └── style.css
        ├── js/
        │   └── script.js
        └── img/
```

## 各主要ファイルの役割

| ファイル・ディレクトリ | 説明 |
|:----------------------|:-----|
| run.py | Flaskアプリ起動ファイル。dotenv読み込み対応 |
| setup_project.py | プロジェクト自動構成スクリプト |
| add_page.py | ページ追加CLIツール。view.pyとindex.htmlをペア生成 |
| requirements.txt | 必要なPythonパッケージ一覧 |
| app/__init__.py | Flaskアプリ初期化、Blueprint登録、ChoiceLoader設定 |
| app/common/ | 共通モジュール。utils.py（ユーティリティ）、filters.py（Jinjaフィルター）、globals.py（Jinjaグローバル変数） |
| app/pages/ | ページ単位の管理ディレクトリ。各ページにview.pyとindex.htmlを配置 |
| app/templates/ | 共通テンプレート(layout.html)置き場 |
| app/static/ | 静的ファイル(css, js, img)置き場 |

## 使い方

1. プロジェクト直下で以下を実行：

```bash
python setup_project.py
```

2. 初期構成がすべて自動生成されます。
4. `requirements.txt` に必要なパッケージを追加し、  
   以下のコマンドでインストールします：

```bash
pip install -r requirements.txt
```

5. 新しいページを作成したい場合：

```bash
python add_page.py /your/new/page
```

例：

```bash
python add_page.py /client/detail
```

これで `app/pages/client/detail/view.py` と `index.html` が自動作成されます。

6. Flaskサーバー起動：

```bash
python run.py
```

ブラウザで `http://localhost:5000/` にアクセスして確認できます。

## 特記事項

- `pages/xxx/index.html` をレンダリングするときは、  
  `render_template("xxx/index.html")` と記述します。
- ページ追加時、すでにview.pyまたはindex.htmlが存在する場合は警告を出して作成を中止します。
- ChoiceLoaderを使用しているため、app/pages以下とapp/templates以下をテンプレート対象にしています。
