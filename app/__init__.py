import os
import sys
from flask import Flask


def get_data_dir():
    """مسیر ذخیره دیتابیس: کنار exe یا کنار پروژه"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return base


def create_app():
    app = Flask(__name__)
    app.config["DATABASE"] = os.path.join(get_data_dir(), "tasks.db")

    from . import db
    db.init_app(app)

    from . import services, themes
    from .routes import tasks, projects, categories, settings, reports
    app.register_blueprint(tasks.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(reports.bp)

    @app.context_processor
    def inject_globals():
        """داده‌هایی که توی همه‌ی صفحات (منوی کناری و تم) لازمه"""
        return {
            "stats": services.compute_stats(),
            "WEEKDAYS": services.WEEKDAY_NAMES,
            "theme": themes.get_active_theme(),   # تم رنگی فعال (۳ رنگ)
        }

    return app
