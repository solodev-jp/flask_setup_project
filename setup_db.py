#!/usr/bin/env python3
"""setup_db.py — final, self-contained

実行すると
  • instance/・migrations/ ディレクトリを確保
  • .env に不足キーを追記（既存値は保持）
  • app/common/db.py, models/user.py, pages/dbtest/* を生成
  • app/__init__.py を .bak 退避後に上書き
  • add_model.py CLI も同時生成（モデル追加を対話式で支援）

※ DATABASE_URL が sqlite:///instance/app.db のような相対指定でも、
   アプリ起動時に絶対パスへ変換して OperationalError を防ぎます。
"""
from __future__ import annotations

import os
import subprocess
import shutil
from pathlib import Path
from typing import Final, List

from dotenv import load_dotenv

# ──────────────────────────────────────────────── 定数 ────────────────────────────────────────────────
ROOT: Final = Path.cwd()
APP_DIR: Final = ROOT / "app"
INSTANCE_DIR: Final = ROOT / "instance"
MIGRATIONS_DIR: Final = ROOT / "migrations"
ENV_PATH: Final = ROOT / ".env"

load_dotenv()

# ────────────────────────────────── .env に不足キーを追記 ──────────────────────────────────
def ensure_env_keys() -> None:
    if not ENV_PATH.exists():
        print("[Error] .env not found — abort.")
        return

    existing = {
        line.split("=")[0].strip()
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }

    extra = {
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "password",
        "MYSQL_HOST": "localhost",
        "MYSQL_DBNAME": "test",
        "SUPABASE_USER": "your_user",
        "SUPABASE_PASSWORD": "your_password",
        "SUPABASE_HOST": "your-host.supabase.co",
        "SUPABASE_DBNAME": "your_database",
    }

    additions: List[str] = [f"{k}={v}\n" for k, v in extra.items() if k not in existing]

    if additions:
        with ENV_PATH.open("a", encoding="utf-8") as fh:
            fh.writelines(additions)
        print("[Update] .env に不足キーを追記しました。")
    else:
        print("[Skip] .env 追記なし。")

# ────────────────────────────── 生成ファイルのテンプレート ──────────────────────────────
DB_PY = (
    "from flask_sqlalchemy import SQLAlchemy\n"
    "from flask_migrate import Migrate\n\n"
    "db = SQLAlchemy()\n"
    "migrate = Migrate()\n"
)

MODELS_INIT = "# app.models package\n"

USER_MODEL = (
    "from app.common.db import db\n\n"
    "class User(db.Model):\n"
    "    __tablename__ = 'users'\n\n"
    "    id   = db.Column(db.Integer, primary_key=True)\n"
    "    name = db.Column(db.String(128))\n\n"
    "    def __repr__(self):\n"
    "        return f'<User {self.id}:{self.name}>'\n"
)

DBTEST_VIEW = (
    "from flask import Blueprint, render_template\n"
    "from app.models.user import User\n\n"
    "bp = Blueprint('dbtest', __name__, url_prefix='/dbtest')\n\n"
    "@bp.route('/')\n"
    "def index():\n"
    "    users = User.query.all()\n"
    "    return render_template('dbtest/index.html', users=users)\n"
)

DBTEST_HTML = (
    "{% extends 'layout.html' %}\n\n"
    "{% block title %}DB Test{% endblock %}\n\n"
    "{% block content %}\n"
    "<h2>DB 接続テストページ</h2>\n"
    "{% if users %}\n"
    "  <ul>\n"
    "  {% for u in users %}<li>{{ u.id }} : {{ u.name }}</li>{% endfor %}\n"
    "  </ul>\n"
    "{% else %}<p>ユーザーが存在しません。</p>{% endif %}\n"
    "{% endblock %}\n"
)

ADD_MODEL = '''#!/usr/bin/env python3
"""add_model.py — モデルファイル生成 CLI + 自動マイグレーション

モデルファイルを作成後、自動で
    - models/__init__.py にインポート追記
    - dbtest/view.py にインポート追記
    - flask db migrate / upgrade を実行
"""

import subprocess
from pathlib import Path

ROOT = Path.cwd()
MODELS_DIR = ROOT / "app" / "models"
DBTEST_VIEW = ROOT / "app" / "pages" / "dbtest" / "view.py"
MODELS_INIT = MODELS_DIR / "__init__.py"

def ask(msg: str, default: str = "") -> str:
    val = input(f"{msg} [{default}]: ").strip()
    return val or default

def append_imports(model_name: str, class_name: str) -> None:
    import_line = f"from app.models.{model_name} import {class_name}\\n"

    # models/__init__.py に追記
    if import_line not in MODELS_INIT.read_text(encoding="utf-8"):
        with MODELS_INIT.open("a", encoding="utf-8") as f:
            f.write(import_line)
        print(f"[Update] models/__init__.py に {class_name} を追加")

    # dbtest/view.py に追記（先頭に追加）
    if DBTEST_VIEW.exists():
        content = DBTEST_VIEW.read_text(encoding="utf-8")
        if import_line not in content:
            DBTEST_VIEW.write_text(import_line + content, encoding="utf-8")
            print(f"[Update] dbtest/view.py に {class_name} をインポート")

def auto_migrate(model_name: str) -> None:
    print("[Step] flask db migrate / upgrade を実行中…")
    try:
        subprocess.run(["flask", "db", "migrate", "-m", f"add {model_name} table"], check=True)
        subprocess.run(["flask", "db", "upgrade"], check=True)
        print("[OK] マイグレーション完了")
    except subprocess.CalledProcessError as e:
        print(f"[Error] マイグレーション失敗: {e}")

def main() -> None:
    table = ask("テーブル名 (例: post)").lower()
    if not table:
        print("テーブル名が空です。中止します。")
        return

    columns: list[tuple[str, str]] = []
    print("\\nカラムを追加します (id は自動追加)")
    print("型例: String(255), Integer, Boolean, DateTime, Text\\n")
    while True:
        name = ask("カラム名 (Enterで終了)")
        if not name:
            break
        type_ = ask("型", "String(255)")
        columns.append((name, type_))

    class_name = table.capitalize()
    lines = [
        "from app.common.db import db\\n\\n",
        f"class {class_name}(db.Model):\\n",
        f"    __tablename__ = '{table}'\\n\\n",
        "    id = db.Column(db.Integer, primary_key=True)\\n",
    ]
    for n, t in columns:
        lines.append(f"    {n} = db.Column(db.{t})\\n")

    repr_fields = ['id'] + [n for n, _ in columns]
    repr_body = ":".join([f"{{self.{f}}}" for f in repr_fields])
    lines += [
        "\\n    def __repr__(self):\\n",
        f"        return f'<{class_name} {repr_body}>'\\n",
    ]

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    fpath = MODELS_DIR / f"{table}.py"
    if fpath.exists():
        print(f"[Error] {fpath.relative_to(ROOT)} は既に存在します。")
        return
    fpath.write_text(''.join(lines), encoding='utf-8')
    print(f"[OK] {fpath.relative_to(ROOT)} を作成しました。")

    append_imports(table, class_name)
    auto_migrate(table)

if __name__ == '__main__':
    main()
'''

APP_INIT = r"""import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

load_dotenv()

def _resolve_sqlite(uri: str | None) -> str | None:
    if uri and uri.startswith('sqlite:///') and not uri.startswith('sqlite:////'):
        return f'sqlite:///{Path(uri[10:]).resolve()}'
    return uri

def _register_blueprints(app: Flask) -> None:
    from importlib import import_module
    base_dir = Path(__file__).parent / 'pages'
    for view_py in base_dir.rglob('view.py'):
        mod_path = '.'.join(view_py.relative_to(Path(__file__).parent).with_suffix('').parts)
        mod = import_module(f'app.{mod_path}')
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp)

def _register_globals(app: Flask) -> None:
    @app.context_processor
    def inject_globals() -> dict:
        return {'now_year': datetime.utcnow().year}

def create_app() -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        instance_path=os.path.join(os.getcwd(), 'instance'),
    )

    app.jinja_loader = ChoiceLoader([
        FileSystemLoader('app/pages'),
        FileSystemLoader('app/templates'),
    ])

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = _resolve_sqlite(os.getenv('DATABASE_URL'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from app.common.db import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)

    _register_blueprints(app)
    try:
        from app.common import globals as globals_module
        app.context_processor(globals_module.inject_globals)
    except ImportError:
        _register_globals(app)

    return app
"""

# ─────────────────────────────── ユーティリティ ───────────────────────────────
def create_file(path: Path, content: str, *, overwrite: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        print(f"[Skip]   {path.relative_to(ROOT)} (exists)")
        return
    path.write_text(content, encoding="utf-8")
    print(f"[{'Overwrite' if overwrite else 'Create'}] {path.relative_to(ROOT)}")

def abs_sqlite_url(raw: str | None) -> str | None:
    if raw and raw.startswith("sqlite:///") and not raw.startswith("sqlite:////"):
        return f"sqlite:///{(ROOT / raw[10:]).resolve()}"
    return raw

# ────────────────────────────────── メイン処理 ─────────────────────────────────
def setup_db() -> None:
    print("[Start] DB setup …")

    ensure_env_keys()
    update_requirements(ROOT / "requirements.txt")

    INSTANCE_DIR.mkdir(exist_ok=True)
    MIGRATIONS_DIR.mkdir(exist_ok=True)

    create_file(APP_DIR / "common/db.py", DB_PY)
    create_file(APP_DIR / "models/__init__.py", MODELS_INIT)
    create_file(APP_DIR / "models/user.py", USER_MODEL)

    # app/__init__.py を上書き
    init_py = APP_DIR / "__init__.py"
    if init_py.exists():
        bak = init_py.with_suffix(".py.bak")
        shutil.copy(init_py, bak)
        print(f"[Backup] {init_py.relative_to(ROOT)} → {bak.name}")
    create_file(init_py, APP_INIT, overwrite=True)

    # /dbtest/
    dbtest_dir = APP_DIR / "pages/dbtest"
    create_file(dbtest_dir / "view.py", DBTEST_VIEW)
    create_file(dbtest_dir / "index.html", DBTEST_HTML)

    # add_model.py
    create_file(ROOT / "add_model.py", ADD_MODEL)

    #
    # DB 接続テスト
    #
    abs_url = abs_sqlite_url(os.getenv("DATABASE_URL"))
    if abs_url:
        try:
            from sqlalchemy import create_engine

            create_engine(abs_url).connect().close()
            print(f"[OK] DB connection succeeded → {abs_url}")
        except Exception as exc:  # pragma: no cover
            print(f"[Warning] DB connection failed: {exc}")

    print("[Done] DB setup completed.")

    run_flask_db_commands()


def update_requirements(requirements_path: Path) -> None:
    required = {
        "flask_sqlalchemy==3.1.1",
        "flask_migrate==4.1.0",
        "sqlalchemy==2.0.40"
    }

    if not requirements_path.exists():
        print("[Create] requirements.txt が存在しないため新規作成します。")
        requirements_path.write_text("\n".join(sorted(required)) + "\n", encoding="utf-8")
        return

    existing = {
        line.strip().split("==")[0]
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    missing = required - existing
    if not missing:
        print("[Skip] requirements.txt に追記は不要です。")
        return

    with requirements_path.open("a", encoding="utf-8") as f:
        for pkg in sorted(missing):
            f.write(pkg + "\n")
    print(f"[Update] requirements.txt に {len(missing)} 件追記しました。")

def run_flask_db_commands() -> None:
    print("[Step] flask db init / migrate / upgrade を実行中…")

    try:
        subprocess.run(["flask", "db", "init"], check=True)
        print("[OK] flask db init 完了")

        subprocess.run(["flask", "db", "migrate"], check=True)
        print("[OK] flask db migrate 完了")

        subprocess.run(["flask", "db", "upgrade"], check=True)
        print("[OK] flask db upgrade 完了")

    except subprocess.CalledProcessError as e:
        print(f"[Error] Flask DB コマンド実行中にエラーが発生しました: {e}")


if __name__ == "__main__":
    setup_db()
