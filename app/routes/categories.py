from flask import Blueprint, request, redirect, url_for
from ..db import get_db

bp = Blueprint("categories", __name__, url_prefix="/categories")


def back():
    return redirect(request.referrer or url_for("tasks.index"))


@bp.route("/add", methods=["POST"])
def add_category():
    name = request.form.get("name", "").strip()[:40]
    if not name:
        return back()

    db = get_db()
    # اسم تکراری نساز
    dup = db.execute(
        "SELECT 1 FROM categories WHERE lower(name) = lower(?)", (name,)
    ).fetchone()
    if not dup:
        count = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        color = count % 4 + 1          # رنگ‌ها به‌ترتیب: 1..4 و دوباره از اول
        db.execute(
            "INSERT INTO categories (name, color) VALUES (?, ?)", (name, color)
        )
        db.commit()
    return back()


@bp.route("/<int:category_id>/delete", methods=["POST"])
def delete_category(category_id):
    # تسک‌های این دسته حذف نمیشن؛ فقط «بدون دسته» میشن (ON DELETE SET NULL)
    db = get_db()
    db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    db.commit()
    return back()