from flask import Blueprint, render_template, request, redirect, url_for
from ..db import get_db
from .. import services as sv

bp = Blueprint("tasks", __name__)

DONE_KINDS = ("all", "routine", "random", "project")


def back():
    """برگشت به صفحه‌ی قبلی"""
    return redirect(request.referrer or url_for("tasks.index"))


def valid_category(db, category_id):
    """اگه دسته وجود نداشت None برمی‌گردونه"""
    if not category_id:
        return None
    ok = db.execute("SELECT 1 FROM categories WHERE id = ?", (category_id,)).fetchone()
    return category_id if ok else None


# ---------------- صفحه‌ی امروز (فقط انجام‌نشده‌ها) ----------------
@bp.route("/")
def index():
    d = sv.today()

    # روتین‌هایی که امروز نوبتشونه
    rows = sv.query_tasks("t.kind IN ('daily','weekly')")
    due_rows = [t for t in rows if sv.is_due(t, d)]
    routines_all = sv.build_items(due_rows, d)
    routines = [i for i in routines_all if not i["done"]]

    # تسک‌های رندم انجام‌نشده، گروه‌بندی‌شده بر اساس دسته
    random_items = sv.build_items(
        sv.query_tasks("t.kind = 'random' AND t.is_done = 0"), d
    )
    categories = sv.get_categories()
    groups = sv.group_by_category(random_items, categories)

    return render_template(
        "index.html",
        routines=routines,
        routines_total=len(routines_all),
        routines_done=len(routines_all) - len(routines),
        groups=groups,
        categories=categories,
        randoms_count=len(random_items),
        today_name=sv.WEEKDAY_NAMES[sv.persian_weekday(d)],
        today_date=d.isoformat(),
    )


# ---------------- صفحه‌ی انجام‌شده‌ها ----------------
@bp.route("/done")
def done():
    db = get_db()
    kind = request.args.get("kind", "all")
    if kind not in DONE_KINDS:
        kind = "all"

    project_id = request.args.get("project", type=int)
    project = None
    if project_id:
        project = db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if project:
            kind = "project"
        else:
            project_id = None

    routines = sv.done_routines_today() if kind in ("all", "routine") else []
    randoms = sv.done_oneoff("random") if kind in ("all", "random") else []
    projs = sv.done_oneoff("project", project_id) if kind in ("all", "project") else []

    return render_template(
        "done.html",
        routines=routines,
        randoms=randoms,
        projs=projs,
        kind=kind,
        project=project,
        total=len(routines) + len(randoms) + len(projs),
    )


# ---------------- مدیریت روتین‌ها ----------------
@bp.route("/routines")
def routines():
    items = sv.build_items(sv.query_tasks("t.kind IN ('daily','weekly')"))
    daily = [i for i in items if i["task"]["kind"] == "daily"]
    weekly = [i for i in items if i["task"]["kind"] == "weekly"]
    return render_template(
        "routines.html", daily=daily, weekly=weekly, today=sv.today()
    )


# ---------------- افزودن تسک ----------------
@bp.route("/tasks/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    kind = request.form.get("kind", "random")
    if not title:
        return back()
    if kind not in sv.KINDS:
        kind = "random"

    db = get_db()
    weekdays = ""
    project_id = None
    category_id = None

    if kind == "weekly":
        days = sorted(
            {
                int(x)
                for x in request.form.getlist("weekdays")
                if x.isdigit() and 0 <= int(x) <= 6
            }
        )
        if not days:
            return back()
        weekdays = ",".join(str(x) for x in days)

    if kind == "project":
        project_id = request.form.get("project_id", type=int)
        exists = db.execute(
            "SELECT 1 FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if not exists:
            return back()

    if kind == "random":
        category_id = valid_category(db, request.form.get("category_id", type=int))

    db.execute(
        "INSERT INTO tasks (title, kind, weekdays, project_id, category_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (title, kind, weekdays, project_id, category_id),
    )
    db.commit()
    return back()


# ---------------- تغییر دسته‌ی تسک رندم ----------------
@bp.route("/tasks/<int:task_id>/category", methods=["POST"])
def set_category(task_id):
    db = get_db()
    category_id = valid_category(db, request.form.get("category_id", type=int))
    db.execute(
        "UPDATE tasks SET category_id = ? WHERE id = ? AND kind = 'random'",
        (category_id, task_id),
    )
    db.commit()
    return back()


# ---------------- تیک زدن ----------------
@bp.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    db = get_db()
    task = db.execute(
        "SELECT kind, is_done FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if not task:
        return back()

    if task["kind"] in sv.RECURRING:
        # تسک تکراری: فقط انجام‌شدن «امروز» ثبت/لغو میشه
        ds = sv.today().isoformat()
        exists = db.execute(
            "SELECT 1 FROM task_logs WHERE task_id = ? AND done_date = ?",
            (task_id, ds),
        ).fetchone()
        if exists:
            db.execute(
                "DELETE FROM task_logs WHERE task_id = ? AND done_date = ?",
                (task_id, ds),
            )
        else:
            db.execute(
                "INSERT OR IGNORE INTO task_logs (task_id, done_date) VALUES (?, ?)",
                (task_id, ds),
            )
    else:
        if task["is_done"]:
            db.execute(
                "UPDATE tasks SET is_done = 0, completed_at = NULL WHERE id = ?",
                (task_id,),
            )
        else:
            db.execute(
                "UPDATE tasks SET is_done = 1, completed_at = datetime('now','localtime') WHERE id = ?",
                (task_id,),
            )
    db.commit()
    return back()


@bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return back()


# ---------------- زیرتسک‌ها ----------------
@bp.route("/tasks/<int:task_id>/subtasks/add", methods=["POST"])
def add_subtask(task_id):
    title = request.form.get("title", "").strip()
    db = get_db()
    task = db.execute("SELECT kind FROM tasks WHERE id = ?", (task_id,)).fetchone()

    # زیرتسک فقط برای تسک‌های پروژه و رندم
    if title and task and task["kind"] not in sv.RECURRING:
        db.execute(
            "INSERT INTO subtasks (task_id, title) VALUES (?, ?)", (task_id, title)
        )
        # اگه تسک اصلی تیک خورده بود و زیرتسک جدید اومد، دوباره بازش کن
        db.execute(
            "UPDATE tasks SET is_done = 0, completed_at = NULL WHERE id = ?", (task_id,)
        )
        db.commit()
    return back()


@bp.route("/subtasks/<int:sub_id>/toggle", methods=["POST"])
def toggle_subtask(sub_id):
    db = get_db()
    sub = db.execute("SELECT * FROM subtasks WHERE id = ?", (sub_id,)).fetchone()
    if sub:
        if sub["is_done"]:
            db.execute(
                "UPDATE subtasks SET is_done = 0, completed_at = NULL WHERE id = ?",
                (sub_id,),
            )
        else:
            db.execute(
                "UPDATE subtasks SET is_done = 1, completed_at = datetime('now','localtime') WHERE id = ?",
                (sub_id,),
            )
        db.commit()
    return back()


@bp.route("/subtasks/<int:sub_id>/delete", methods=["POST"])
def delete_subtask(sub_id):
    db = get_db()
    db.execute("DELETE FROM subtasks WHERE id = ?", (sub_id,))
    db.commit()
    return back()