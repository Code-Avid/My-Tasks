"""تم‌های رنگی: پالت‌های پیش‌فرض، اعتبارسنجی کد رنگ و ذخیره/خواندن از دیتابیس

هر تم دقیقاً ۳ رنگ داره و کل ظاهر پروژه (توسط static/js/theme-engine.js) از همین ۳ رنگ ساخته می‌شه:
    bg      رنگ ۱ · پس‌زمینه
    main    رنگ ۲ · اصلی
    accent  رنگ ۳ · تأکیدی
"""
import re

from .db import get_db

# تم‌های پیش‌فرض (با هر بار اجرا با همین مقادیر هماهنگ می‌شن؛ کاربر نمی‌تونه ویرایششون کنه
# ولی می‌تونه از روی اون‌ها یک تم کاستوم بسازه)
PRESETS = [
    {"slug": "black-purple-cyan", "name": "مشکی، بنفش، فیروزه‌ای",
     "bg": "#07070d", "main": "#a855f7", "accent": "#00e5ff"},
    {"slug": "white-gray-iceblue", "name": "سفید، خاکستری، آبی یخی",
     "bg": "#f8fafc", "main": "#6b7280", "accent": "#8fd3ff"},
    {"slug": "navy-teal-white", "name": "سرمه‌ای، سبزآبی، سفید",
     "bg": "#0b1f3a", "main": "#14b8a6", "accent": "#ffffff"},
    {"slug": "pink-white-lavender", "name": "صورتی پاستلی، سفید، لاوندر",
     "bg": "#ffd9e8", "main": "#ffffff", "accent": "#b79cf2"},
]
DEFAULT_SLUG = PRESETS[0]["slug"]
MAX_CUSTOM = 30

_HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB = re.compile(
    r"^(?:rgb\(\s*)?(\d{1,3})\s*[,\s]\s*(\d{1,3})\s*[,\s]\s*(\d{1,3})\s*\)?$", re.I
)


def normalize_color(value):
    """
    کد رنگ رو (HEX یا RGB) به فرم استاندارد '#rrggbb' تبدیل می‌کنه.
    ورودی‌های قابل قبول:  '#a855f7'  |  'a855f7'  |  '#fff'  |  '168, 85, 247'  |  'rgb(168,85,247)'
    اگه نامعتبر بود None برمی‌گردونه.
    """
    s = (value or "").strip()

    m = _HEX.match(s)
    if m:
        h = m.group(1).lower()
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return "#" + h

    m = _RGB.match(s)
    if m:
        r, g, b = (int(x) for x in m.groups())
        if max(r, g, b) <= 255:
            return "#%02x%02x%02x" % (r, g, b)
    return None


def _to_dict(row):
    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": row["name"],
        "bg": row["c_bg"],
        "main": row["c_main"],
        "accent": row["c_accent"],
        "builtin": bool(row["is_builtin"]),
    }


def _set_setting(db, key, value):
    db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value))
    )


def _get_setting(db, key):
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


# ---------- راه‌اندازی (از db.init_db صدا زده می‌شه) ----------
def seed_defaults(db):
    """تم‌های پیش‌فرض رو می‌سازه/به‌روز می‌کنه و اگه تم فعالی نبود، پیش‌فرض رو فعال می‌کنه"""
    for p in PRESETS:
        row = db.execute("SELECT id FROM themes WHERE slug = ?", (p["slug"],)).fetchone()
        if row:
            db.execute(
                "UPDATE themes SET name = ?, c_bg = ?, c_main = ?, c_accent = ?, is_builtin = 1 "
                "WHERE id = ?",
                (p["name"], p["bg"], p["main"], p["accent"], row["id"]),
            )
        else:
            db.execute(
                "INSERT INTO themes (slug, name, c_bg, c_main, c_accent, is_builtin) "
                "VALUES (?, ?, ?, ?, ?, 1)",
                (p["slug"], p["name"], p["bg"], p["main"], p["accent"]),
            )

    active = _get_setting(db, "active_theme_id")
    valid = (
        active is not None
        and active.isdigit()
        and db.execute("SELECT 1 FROM themes WHERE id = ?", (int(active),)).fetchone()
    )
    if not valid:
        default = db.execute(
            "SELECT id FROM themes WHERE slug = ?", (DEFAULT_SLUG,)
        ).fetchone()
        _set_setting(db, "active_theme_id", default["id"])


# ---------- خواندن ----------
def list_themes():
    """اول تم‌های پیش‌فرض، بعد کاستوم‌ها (به ترتیب ساخت)"""
    rows = get_db().execute(
        "SELECT * FROM themes ORDER BY is_builtin DESC, id"
    ).fetchall()
    return [_to_dict(r) for r in rows]


def get_active_theme():
    db = get_db()
    row = None
    active = _get_setting(db, "active_theme_id")
    if active and active.isdigit():
        row = db.execute("SELECT * FROM themes WHERE id = ?", (int(active),)).fetchone()
    if row is None:
        row = db.execute("SELECT * FROM themes WHERE slug = ?", (DEFAULT_SLUG,)).fetchone()
    if row is None:  # نباید پیش بیاد؛ فقط برای اطمینان
        p = PRESETS[0]
        return {"id": 0, "slug": p["slug"], "name": p["name"], "bg": p["bg"],
                "main": p["main"], "accent": p["accent"], "builtin": True}
    return _to_dict(row)


# ---------- نوشتن ----------
def set_active(theme_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM themes WHERE id = ?", (theme_id,)).fetchone():
        return False
    _set_setting(db, "active_theme_id", theme_id)
    db.commit()
    return True


def create_custom(name, bg, main, accent):
    """تم کاستوم جدید می‌سازه و id رو برمی‌گردونه (اگه سقف مجاز پر بود None)"""
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM themes WHERE is_builtin = 0").fetchone()[0]
    if count >= MAX_CUSTOM:
        return None
    cur = db.execute(
        "INSERT INTO themes (name, c_bg, c_main, c_accent, is_builtin) VALUES (?, ?, ?, ?, 0)",
        (name, bg, main, accent),
    )
    db.commit()
    return cur.lastrowid


def delete_custom(theme_id):
    """فقط تم‌های کاستوم حذف می‌شن. اگه تم فعال بود، پیش‌فرض فعال می‌شه."""
    db = get_db()
    was_active = _get_setting(db, "active_theme_id") == str(theme_id)
    cur = db.execute("DELETE FROM themes WHERE id = ? AND is_builtin = 0", (theme_id,))
    if not cur.rowcount:
        return False
    if was_active:
        default = db.execute(
            "SELECT id FROM themes WHERE slug = ?", (DEFAULT_SLUG,)
        ).fetchone()
        _set_setting(db, "active_theme_id", default["id"])
    db.commit()
    return True
