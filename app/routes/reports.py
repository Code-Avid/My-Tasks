from datetime import datetime, timedelta
from flask import Blueprint, render_template, request
from ..db import get_db

bp = Blueprint("reports", __name__, url_prefix="/reports")

PERIODS = {
    "today": "امروز",
    "week": "این هفته",
    "month": "۳۰ روز اخیر",
    "season": "۹۰ روز اخیر (فصل)",
}


def get_range(period):
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "week":
        # هفته ایرانی از شنبه شروع میشه (weekday: دوشنبه=0 ... شنبه=5)
        start = today - timedelta(days=(today.weekday() + 2) % 7)
    elif period == "month":
        start = today - timedelta(days=30)
    elif period == "season":
        start = today - timedelta(days=90)
    else:  # today
        start = today
    return start.strftime("%Y-%m-%d %H:%M:%S")


@bp.route("/")
def report():
    period = request.args.get("period", "week")
    if period not in PERIODS:
        period = "week"
    start = get_range(period)
    start_date = start[:10]

    db = get_db()

    # روتین‌ها: هر تسک تکراری چند بار انجام شده
    routines = db.execute(
        """SELECT t.id, t.title, t.kind, COUNT(*) AS c, MAX(l.done_date) AS last_date
           FROM task_logs l JOIN tasks t ON t.id = l.task_id
           WHERE l.done_date >= ?
           GROUP BY t.id
           ORDER BY c DESC""",
        (start_date,),
    ).fetchall()

    # تسک‌های پروژه و رندم
    tasks = db.execute(
        """SELECT t.*, p.name AS project_name
           FROM tasks t LEFT JOIN projects p ON p.id = t.project_id
           WHERE t.is_done = 1 AND t.kind IN ('project','random')
                 AND t.completed_at >= ?
           ORDER BY t.completed_at DESC""",
        (start,),
    ).fetchall()

    subtasks = db.execute(
        """SELECT s.*, t.title AS parent_title FROM subtasks s
           JOIN tasks t ON t.id = s.task_id
           WHERE s.is_done = 1 AND s.completed_at >= ?
           ORDER BY s.completed_at DESC""",
        (start,),
    ).fetchall()

    return render_template(
        "reports.html",
        routines=routines,
        routine_total=sum(r["c"] for r in routines),
        tasks=tasks,
        subtasks=subtasks,
        period=period,
        periods=PERIODS,
    )


