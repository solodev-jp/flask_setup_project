import os
from pathlib import Path

# 各ファイルのテンプレート
TEMPLATES = {
    ".gitignore": """# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
env/
venv/
ENV/
.Python

# Flask
instance/
*.sqlite3
*.db
*.log

# IDE
.vscode/
.idea/
*.sublime-project
*.sublime-workspace

# OS
.DS_Store
Thumbs.db
""",
    ".env": """FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/app.db
""",
    "run.py": """from app import create_app
from dotenv import load_dotenv
import os

load_dotenv()

app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development")
""",
    "app/__init__.py": """import os
import importlib
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

def create_app():
    app = Flask(__name__)
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader("app/pages"),
        FileSystemLoader("app/templates"),
    ])
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    try:
        from app.common.db import db
        db.init_app(app)
    except ImportError:
        pass

    register_blueprints(app)
    register_filters(app)
    register_globals(app)

    return app

def register_blueprints(app):
    register_blueprint_group(app, "pages")

def register_blueprint_group(app, group):
    base_dir = os.path.join(os.path.dirname(__file__), group)
    if not os.path.exists(base_dir):
        return
    for root, dirs, files in os.walk(base_dir):
        if "view.py" in files:
            rel_path = os.path.relpath(root, base_dir)
            module_path = f"app.{group}." + rel_path.replace(os.path.sep, ".") + ".view"
            module = importlib.import_module(module_path)
            app.register_blueprint(module.bp)

def register_filters(app):
    try:
        from app.common import filters
        for name, func in filters.FILTERS.items():
            app.jinja_env.filters[name] = func
    except ImportError:
        pass

def register_globals(app):
    try:
        from app.common import globals
        app.context_processor(globals.inject_globals)
    except ImportError:
        pass
""",
    "app/common/utils.py": """# Utility functions

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")
""",
    "app/common/filters.py": """# Jinja2 filters

def reverse_string(s):
    return s[::-1]

def uppercase(s):
    return s.upper()

FILTERS = {
    "reverse": reverse_string,
    "uppercase": uppercase,
}
""",
    "app/common/globals.py": """# Jinja2 globals

import datetime

def inject_globals():
    return {
        "site_name": "My Flask Site",
        "now_year": lambda: datetime.datetime.now().year,
    }
""",
    "app/templates/layout.html": """<!doctype html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <title>{% block title %}My Flask Site{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <h1>My Flask Site</h1>
        <nav>
            <a href="/">Home</a>
        </nav>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer>
        <small>&copy; {{ now_year() }} My Flask Site</small>
    </footer>
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
""",
    "app/static/css/style.css": """/* Default Styles */
body {
    font-family: sans-serif;
}
""",
    "app/static/js/script.js": """// Default Scripts
console.log("Hello, Flask static files!");
""",
    "app/pages/index/view.py": """from flask import Blueprint, render_template

bp = Blueprint('index', __name__, url_prefix='/')

@bp.route("/")
def index():
    return render_template("index/index.html", title="Top Page")
""",
    "app/pages/index/index.html": """{% extends "layout.html" %}

{% block title %}Top Page{% endblock %}

{% block content %}
<h2>ようこそ！</h2>
<p>現在の年: {{ now_year() }}</p>
{% endblock %}
""",
    "add_page.py": """import os
from pathlib import Path

def create_page(path):
    parts = path.strip('/').split('/')
    page_dir = Path('app/pages') / Path(*parts)

    view_path = page_dir / 'view.py'
    template_path = page_dir / 'index.html'

    if view_path.exists() or template_path.exists():
        print(f"[Warning] {page_dir} already exists with view.py or index.html!")
        return

    page_dir.mkdir(parents=True, exist_ok=True)

    route_url = '/' + '/'.join(parts)
    view_content = f\"\"\"from flask import Blueprint, render_template

bp = Blueprint('{ '_'.join(parts) }', __name__, url_prefix='{route_url}')

@bp.route("/")
def index():
    return render_template("{'/'.join(parts)}/index.html", title="{parts[-1].capitalize()} Page")
\"\"\"
    view_path.write_text(view_content)
    print(f"[Create] {view_path}")

    html_content = \"\"\"{% extends "layout.html" %}

{% block title %}New Page{% endblock %}

{% block content %}
<h2>New Page Created</h2>
{% endblock %}
\"\"\"
    template_path.write_text(html_content)
    print(f"[Create] {template_path}")

    create_init_pys_for_page(page_dir)

def create_init_pys_for_page(page_dir):
    current = page_dir
    while current != Path("app/pages"):
        init_path = current / "__init__.py"
        if not init_path.exists():
            module_path = str(init_path.parent).replace(os.sep, ".").replace("app.", "app.")
            init_path.write_text(f"# {module_path} package\\n")
            print(f"[Create] {init_path}")
        current = current.parent

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python add_page.py <path/to/page>")
    else:
        create_page(sys.argv[1])
"""
}

# ファイル作成
def create_file(path, content=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content)
        print(f"[Create] {path}")
    else:
        print(f"[Skip] {path} already exists.")

# 必要な各ディレクトリに__init__.pyを作る
def create_init_py(directory):
    path = Path(directory) / "__init__.py"
    if not path.exists():
        module_path = str(path.parent).replace(os.sep, ".").replace("app.", "app.")
        path.write_text(f"# {module_path} package\n")
        print(f"[Create] {path}")
    else:
        print(f"[Skip] {path} already exists.")

# setup_project本体
def setup_project():
    for file_path, content in TEMPLATES.items():
        target = Path(file_path)
        create_file(target, content)
        if target.parts[0] == "app":
            for i in range(1, len(target.parts)):
                partial = Path(*target.parts[:i])
                if partial.is_dir():
                    create_init_py(partial)

    create_init_py(Path("app"))
    create_init_py(Path("app/pages"))
    create_init_py(Path("app/pages/index"))
    create_init_py(Path("app/common"))

    # requirements.txt を出力
    req_path = Path("requirements.txt")
    if not req_path.exists():
        req_path.write_text(
            "Flask==3.1.0\n"
            "click==8.1.8\n"
            "dotenv==0.9.9\n"
            "python-dotenv==1.1.0\n",
            encoding="utf-8"
        )
        print(f"[Create] {req_path}")
    else:
        print(f"[Skip] {req_path} already exists.")

if __name__ == "__main__":
    setup_project()
