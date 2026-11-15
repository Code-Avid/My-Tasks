from flask import Blueprint, render_template, request, redirect, url_for
from .. import themes

bp = Blueprint("settings", __name__, url_prefix="/settings")

# پیام‌هایی که بعد از هر عملیات بالای صفحه نشون داده می‌شه: کد → (نوع، متن)
MESSAGES = {
    "saved": ("ok", "تم جدید ذخیره و اعمال شد ✔"),
    "applied": ("ok", "تم اعمال شد ✔"),
    "deleted": ("ok", "تم حذف شد."),
    "bad_color": ("err", "یکی از کدهای رنگ نامعتبر بود. HEX مثل #a855f7 یا RGB مثل 168, 85, 247 بنویس."),
    "limit": ("err", "تعداد تم‌های کاستوم به سقف مجاز رسیده. اول چندتا رو حذف کن."),
    "missing": ("err", "این تم پیدا نشد."),
}


def done(code):
    return redirect(url_for("settings.index", msg=code))


@bp.route("/")
def index():
    return render_template(
        "settings.html",
        themes=themes.list_themes(),
        message=MESSAGES.get(request.args.get("msg")),
    )


@bp.route("/theme/<int:theme_id>/apply", methods=["POST"])
def apply_theme(theme_id):
    return done("applied" if themes.set_active(theme_id) else "missing")


@bp.route("/theme/save", methods=["POST"])
def save_theme():
    """ساخت تم کاستوم جدید از ۳ کد رنگ (HEX یا RGB) و اعمال فوری"""
    name = request.form.get("name", "").strip()[:40] or "تم من"
    colors = [
        themes.normalize_color(request.form.get(key))
        for key in ("c_bg", "c_main", "c_accent")
    ]
    if None in colors:
        return done("bad_color")

    new_id = themes.create_custom(name, *colors)
    if new_id is None:
        return done("limit")
    themes.set_active(new_id)
    return done("saved")


@bp.route("/theme/<int:theme_id>/delete", methods=["POST"])
def delete_theme(theme_id):
    return done("deleted" if themes.delete_custom(theme_id) else "missing")
