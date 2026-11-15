import os
import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _migrate(db):
    """آپگرید دیتابیس‌های قدیمی (بدون از دست رفتن اطلاعات)"""
    cols = {r["name"] for r in db.execute("PRAGMA table_info(tasks)")}
    if "kind" not in cols:
        db.execute("ALTER TABLE tasks ADD COLUMN kind TEXT NOT NULL DEFAULT 'random'")
    if "weekdays" not in cols:
        db.execute("ALTER TABLE tasks ADD COLUMN weekdays TEXT NOT NULL DEFAULT ''")
    if "project_id" not in cols:
        db.execute(
            "ALTER TABLE tasks ADD COLUMN project_id INTEGER "
            "REFERENCES projects(id) ON DELETE CASCADE"
        )
    if "category_id" not in cols:
        db.execute(
            "ALTER TABLE tasks ADD COLUMN category_id INTEGER "
            "REFERENCES categories(id) ON DELETE SET NULL"
        )


def init_db():
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, encoding="utf-8") as f:
        db.executescript(f.read())
    _migrate(db)

    # import محلی: چون themes خودش از db استفاده می‌کنه (جلوگیری از import حلقوی)
    from . import themes
    themes.seed_defaults(db)

    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
