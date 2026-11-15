"""منطق مشترک: تاریخ، زمان‌بندی، ساخت آیتم‌های کارت، دسته‌بندی و آمار/XP"""
from datetime import date, timedelta

from .db import get_db

# هفته ایرانی: 0=شنبه ... 6=جمعه
WEEKDAY_NAMES = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]

# شنبه روز اول هفته حساب میشه
ODD_DAYS = [0, 2, 4]    # شنبه، دوشنبه، چهارشنبه
EVEN_DAYS = [1, 3, 5]   # یکشنبه، سه‌شنبه، پنجشنبه

KINDS = {
    "daily": "روزانه",
    "weekly": "هفتگی",
    "project": "پروژه",
    "random": "رندم",
}
RECURRING = ("daily", "weekly")


# ---------- تاریخ ----------
def today():
    return date.today()


def persian_weekday(d):
    """پایتون: دوشنبه=0 ... یکشنبه=6  →  ایرانی: شنبه=0 ... جمعه=6"""
    return (d.weekday() + 2) % 7


def parse_days(s):
    return sorted({int(x) for x in (s or "").split(",") if x.strip().isdigit()})


def is_due(task, d):
    """آیا این تسک تکراری برای روز d باید انجام بشه؟"""
    if task["kind"] == "daily":
        return True
    if task["kind"] == "weekly":
        return persian_weekday(d) in parse_days(task["weekdays"])
    return False


def schedule_label(task):
    if task["kind"] == "daily":
        return "هر روز"
    days = parse_days(task["weekdays"])
    if days == ODD_DAYS:
        return "روزهای فرد (ش، ۲ش، ۴ش)"
    if days == EVEN_DAYS:
        return "روزهای زوج (۱ش، ۳ش، ۵ش)"
    return "، ".join(WEEKDAY_NAMES[i] for i in days)


# ---------- کوئری و ساخت آیتم کارت ----------
def query_tasks(where="1=1", params=(), order="t.id DESC"):
    """where و order فقط از کد خود برنامه میان (نه ورودی کاربر)"""
    return get_db().execute(
        f"""SELECT t.*,
                   p.name  AS project_name,
                   c.name  AS category_name,
                   c.color AS category_color
            FROM tasks t
            LEFT JOIN projects   p ON p.id = t.project_id
            LEFT JOIN categories c ON c.id = t.category_id
            WHERE {where}
            ORDER BY {order}""",
        params,
    ).fetchall()


def build_items(rows, day=None):
    """هر ردیف تسک رو به دیکشنری آماده‌ی نمایش تبدیل می‌کنه"""
    db = get_db()
    day_str = (day or today()).isoformat()
    items = []

    for t in rows:
        recurring = t["kind"] in RECURRING
        item = {
            "task": t,
            "recurring": recurring,
            "subtasks": [],
            "total": 0,
            "done_count": 0,
            "pct": 0,
            "done": False,
            "times": 0,
            "schedule": "",
        }

        if recurring:
            item["done"] = (
                db.execute(
                    "SELECT 1 FROM task_logs WHERE task_id = ? AND done_date = ?",
                    (t["id"], day_str),
                ).fetchone()
                is not None
            )
            item["times"] = db.execute(
                "SELECT COUNT(*) FROM task_logs WHERE task_id = ?", (t["id"],)
            ).fetchone()[0]
            item["pct"] = 100 if item["done"] else 0
            item["schedule"] = schedule_label(t)
        else:
            subs = db.execute(
                "SELECT * FROM subtasks WHERE task_id = ? ORDER BY id", (t["id"],)
            ).fetchall()
            item["subtasks"] = subs
            item["total"] = len(subs)
            item["done_count"] = sum(1 for s in subs if s["is_done"])
            item["done"] = bool(t["is_done"])
            if subs:
                item["pct"] = round(item["done_count"] * 100 / len(subs))
            else:
                item["pct"] = 100 if item["done"] else 0

        items.append(item)
    return items


# ---------- دسته‌بندی ----------
def get_categories():
    return get_db().execute("SELECT * FROM categories ORDER BY id").fetchall()


def group_by_category(items, categories):
    """
    لیست گروه‌ها: اول «بدون دسته» بعد هر دسته (حتی اگه خالی باشه).
    هر گروه: {"category": Row یا None, "cards": [...]}
    """
    by_id = {c["id"]: [] for c in categories}
    uncategorized = []
    for i in items:
        cid = i["task"]["category_id"]
        if cid in by_id:
            by_id[cid].append(i)
        else:
            uncategorized.append(i)

    groups = [{"category": None, "cards": uncategorized}]
    for c in categories:
        groups.append({"category": c, "cards": by_id[c["id"]]})
    return groups


# ---------- انجام‌شده‌ها ----------
def done_routines_today(day=None):
    """روتین‌هایی که امروز تیک خوردن"""
    ds = (day or today()).isoformat()
    rows = query_tasks(
        "t.kind IN ('daily','weekly') "
        "AND t.id IN (SELECT task_id FROM task_logs WHERE done_date = ?)",
        (ds,),
    )
    return build_items(rows, day)


def done_oneoff(kind, project_id=None):
    """تسک‌های تکی (random یا project) انجام‌شده، تازه‌ترین اول"""
    where = "t.is_done = 1 AND t.kind = ?"
    params = [kind]
    if project_id:
        where += " AND t.project_id = ?"
        params.append(project_id)
    return build_items(query_tasks(where, tuple(params), "t.completed_at DESC"))


# ---------- آمار، XP و استریک ----------
def compute_stats():
    db = get_db()
    d = today()
    ds = d.isoformat()

    one_off_done = db.execute(
        "SELECT COUNT(*) FROM tasks WHERE is_done = 1 AND kind IN ('project','random')"
    ).fetchone()[0]
    logs = db.execute("SELECT COUNT(*) FROM task_logs").fetchone()[0]
    logs_today = db.execute(
        "SELECT COUNT(*) FROM task_logs WHERE done_date = ?", (ds,)
    ).fetchone()[0]
    subs = db.execute("SELECT COUNT(*) FROM subtasks WHERE is_done = 1").fetchone()[0]

    xp = (one_off_done + logs) * 10 + subs * 3

    # روتین‌های امروز
    routines = db.execute(
        "SELECT * FROM tasks WHERE kind IN ('daily','weekly')"
    ).fetchall()
    due = [t for t in routines if is_due(t, d)]
    done_ids = {
        r["task_id"]
        for r in db.execute("SELECT task_id FROM task_logs WHERE done_date = ?", (ds,))
    }
    today_done = sum(1 for t in due if t["id"] in done_ids)

    # استریک: روزهای پشت‌سرهم که حداقل یک کار انجام شده
    rows = db.execute(
        """SELECT DISTINCT done_date FROM task_logs
           UNION
           SELECT DISTINCT substr(completed_at, 1, 10) FROM tasks
           WHERE is_done = 1 AND completed_at IS NOT NULL"""
    ).fetchall()
    days = {r[0] for r in rows}
    cur = d if ds in days else d - timedelta(days=1)
    streak = 0
    while cur.isoformat() in days:
        streak += 1
        cur -= timedelta(days=1)

    projects = db.execute(
        "SELECT id, name FROM projects WHERE is_archived = 0 ORDER BY id DESC LIMIT 6"
    ).fetchall()

    return {
        "xp": xp,
        "level": xp // 100 + 1,
        "xp_in_level": xp % 100,
        "streak": streak,
        "today_total": len(due),
        "today_done": today_done,
        "done_total": one_off_done + logs_today,
        "projects": projects,
    }