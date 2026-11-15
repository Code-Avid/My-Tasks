from flask import Blueprint, render_template, request, redirect, url_for, abort
from ..db import get_db
from .. import services as sv

bp = Blueprint("projects", __name__, url_prefix="/projects")


@bp.route("/")
def list_projects():
    db = get_db()
    projects = []
    for p in db.execute(
        "SELECT * FROM projects WHERE is_archived = 0 ORDER BY id DESC"
    ).fetchall():
        c = db.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(is_done), 0) AS done "
            "FROM tasks WHERE project_id = ?",
            (p["id"],),
        ).fetchone()
        pct = round(c["done"] * 100 / c["total"]) if c["total"] else 0
        projects.append(
            {"project": p, "total": c["total"], "done": c["done"], "pct": pct}
        )
    return render_template("projects.html", projects=projects)


@bp.route("/add", methods=["POST"])
def add_project():
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("projects.list_projects"))
    db = get_db()
    cur = db.execute("INSERT INTO projects (name) VALUES (?)", (name,))
    db.commit()
    return redirect(url_for("projects.detail", project_id=cur.lastrowid))


@bp.route("/<int:project_id>")
def detail(project_id):
    db = get_db()
    project = db.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    if not project:
        abort(404)

    all_items = sv.build_items(
        sv.query_tasks("t.project_id = ?", (project_id,))
    )
    # فقط انجام‌نشده‌ها؛ انجام‌شده‌ها توی صفحه‌ی /done?project=ID هستن
    items = [i for i in all_items if not i["done"]]

    return render_template(
        "project_detail.html",
        project=project,
        items=items,
        total=len(all_items),
        done=len(all_items) - len(items),
    )


@bp.route("/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):
    db = get_db()
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    db.commit()
    return redirect(url_for("projects.list_projects"))


