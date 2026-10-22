"""Administrator console: catalogue CRUD, application triage, notices, messages."""
from __future__ import annotations

import re
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from .. import config
from ..database import db_dependency
from ..security import require_admin
from ..services import (
    APPLICATION_SELECT,
    application_stats,
    enrich_application,
    set_status,
)
from ..templating import redirect, render

router = APIRouter(prefix="/admin")

STATUS_OPTIONS = list(config.STATUS_META.keys())


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "scholarship"


def _unique_slug(conn: sqlite3.Connection, base: str, current_id: int | None = None) -> str:
    slug, n = base, 2
    while True:
        row = conn.execute(
            "SELECT id FROM scholarships WHERE slug = ? AND id IS NOT ?", (slug, current_id)
        ).fetchone()
        if not row:
            return slug
        slug = f"{base}-{n}"
        n += 1


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    totals = {
        "students": conn.execute("SELECT COUNT(*) n FROM users WHERE role = 'student'").fetchone()["n"],
        "scholarships": conn.execute("SELECT COUNT(*) n FROM scholarships").fetchone()["n"],
        "applications": conn.execute("SELECT COUNT(*) n FROM applications").fetchone()["n"],
        "messages": conn.execute(
            "SELECT COUNT(*) n FROM contact_messages WHERE status = 'new'"
        ).fetchone()["n"],
    }
    by_status = {
        r["status"]: r["n"]
        for r in conn.execute("SELECT status, COUNT(*) n FROM applications GROUP BY status").fetchall()
    }
    awarded = conn.execute(
        """SELECT COALESCE(SUM(s.amount_value), 0) v FROM applications a
           JOIN scholarships s ON s.id = a.scholarship_id
           WHERE a.status IN ('approved','disbursed')"""
    ).fetchone()["v"]
    max_status = max(by_status.values()) if by_status else 1

    recent_apps = [
        enrich_application(r)
        for r in conn.execute(
            APPLICATION_SELECT + " ORDER BY a.updated_at DESC LIMIT 8"
        ).fetchall()
    ]
    recent_messages = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 4"
        ).fetchall()
    ]
    top_schemes = [
        dict(r)
        for r in conn.execute(
            """SELECT s.name, s.slug, COUNT(a.id) n FROM applications a
               JOIN scholarships s ON s.id = a.scholarship_id
               GROUP BY s.id ORDER BY n DESC LIMIT 5"""
        ).fetchall()
    ]
    students = conn.execute(
        """SELECT u.id, u.full_name, u.email, u.state, COUNT(a.id) apps
           FROM users u LEFT JOIN applications a ON a.user_id = u.id
           WHERE u.role = 'student' GROUP BY u.id ORDER BY apps DESC, u.id DESC LIMIT 5"""
    ).fetchall()

    return render(
        request,
        "admin/dashboard.html",
        user=user,
        admin_active="dashboard",
        totals=totals,
        by_status=by_status,
        max_status=max_status,
        awarded=awarded,
        recent_apps=recent_apps,
        recent_messages=recent_messages,
        top_schemes=top_schemes,
        students=students,
        status_options=STATUS_OPTIONS,
    )


# --------------------------------------------------------------------------- #
# Scholarships
# --------------------------------------------------------------------------- #
@router.get("/scholarships", response_class=HTMLResponse)
def admin_scholarships(
    request: Request,
    q: str = "",
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    if q:
        like = f"%{q.strip()}%"
        rows = conn.execute(
            "SELECT * FROM scholarships WHERE name LIKE ? OR provider LIKE ? OR state LIKE ? ORDER BY id DESC",
            (like, like, like),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM scholarships ORDER BY id DESC").fetchall()
    return render(
        request,
        "admin/scholarships.html",
        user=user,
        admin_active="scholarships",
        scholarships=[dict(r) for r in rows],
        q=q,
        total=len(rows),
    )


@router.get("/scholarships/new", response_class=HTMLResponse)
def admin_scholarship_new(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    return render(
        request,
        "admin/scholarship_form.html",
        user=user,
        admin_active="scholarships",
        sch={},
        mode="create",
        error=None,
        categories=config.CATEGORY_VALUES,
        levels=config.LEVELS,
        states=config.STATES,
    )


@router.get("/scholarships/{sid}/edit", response_class=HTMLResponse)
def admin_scholarship_edit(
    request: Request,
    sid: int,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    row = conn.execute("SELECT * FROM scholarships WHERE id = ?", (sid,)).fetchone()
    if not row:
        return redirect("/admin/scholarships", "Scholarship not found.", "error")
    return render(
        request,
        "admin/scholarship_form.html",
        user=user,
        admin_active="scholarships",
        sch=dict(row),
        mode="edit",
        error=None,
        categories=config.CATEGORY_VALUES,
        levels=config.LEVELS,
        states=config.STATES,
    )


SCHOLARSHIP_FIELDS = [
    "name", "provider", "category", "level", "state", "amount", "amount_value",
    "deadline", "description", "eligibility", "benefits", "documents", "apply_mode",
    "official_link", "tags", "income_limit", "gender", "minority", "disability",
    "featured", "status",
]


def _scholarship_payload(form: dict) -> dict:
    def as_int(key: str, default: int = 0) -> int:
        raw = str(form.get(key, "")).replace(",", "").strip()
        return int(raw) if raw.isdigit() else default

    payload = {
        "name": " ".join(str(form.get("name", "")).split()),
        "provider": " ".join(str(form.get("provider", "")).split()),
        "category": form.get("category") or "Central Government",
        "level": form.get("level") or "Undergraduate",
        "state": form.get("state") or "All India",
        "amount": form.get("amount", "").strip() or "As per scheme norms",
        "amount_value": as_int("amount_value"),
        "deadline": form.get("deadline") or date.today().isoformat(),
        "description": form.get("description", "").strip(),
        "eligibility": form.get("eligibility", "").strip(),
        "benefits": form.get("benefits", "").strip(),
        "documents": form.get("documents", "").strip(),
        "apply_mode": form.get("apply_mode", "").strip() or "Online",
        "official_link": form.get("official_link", "").strip() or "https://scholarships.gov.in",
        "tags": form.get("tags", "").strip(),
        "income_limit": as_int("income_limit"),
        "gender": form.get("gender") or "Any",
        "minority": 1 if form.get("minority") else 0,
        "disability": 1 if form.get("disability") else 0,
        "featured": 1 if form.get("featured") else 0,
        "status": form.get("status") or "open",
    }
    return payload


@router.post("/scholarships", response_class=HTMLResponse)
async def admin_scholarship_create(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    form = dict(await request.form())
    payload = _scholarship_payload(form)
    if len(payload["name"]) < 4 or len(payload["provider"]) < 3:
        return render(
            request, "admin/scholarship_form.html", user=user, admin_active="scholarships",
            sch=payload, mode="create", status_code=422,
            error="Scheme name and provider are required.",
            categories=config.CATEGORY_VALUES, levels=config.LEVELS, states=config.STATES,
        )
    payload["slug"] = _unique_slug(conn, form.get("slug", "").strip() or _slugify(payload["name"]))
    cols = list(payload.keys())
    conn.execute(
        f"INSERT INTO scholarships ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
        [payload[c] for c in cols],
    )
    return redirect("/admin/scholarships", f"“{payload['name']}” added to the catalogue.")


@router.post("/scholarships/{sid}", response_class=HTMLResponse)
async def admin_scholarship_update(
    request: Request,
    sid: int,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    existing = conn.execute("SELECT * FROM scholarships WHERE id = ?", (sid,)).fetchone()
    if not existing:
        return redirect("/admin/scholarships", "Scholarship not found.", "error")

    form = dict(await request.form())
    payload = _scholarship_payload(form)
    payload["slug"] = _unique_slug(
        conn, form.get("slug", "").strip() or _slugify(payload["name"]), current_id=sid
    )
    form_sch = {**payload, "id": sid}
    if len(payload["name"]) < 4 or len(payload["provider"]) < 3:
        return render(
            request, "admin/scholarship_form.html", user=user, admin_active="scholarships",
            sch=form_sch, mode="edit", status_code=422,
            error="Scheme name and provider are required.",
            categories=config.CATEGORY_VALUES, levels=config.LEVELS, states=config.STATES,
        )
    sets = ", ".join(f"{c} = ?" for c in payload)
    conn.execute(
        f"UPDATE scholarships SET {sets} WHERE id = ?",
        [*payload.values(), sid],
    )
    return redirect("/admin/scholarships", f"“{payload['name']}” updated.")


@router.post("/scholarships/{sid}/delete")
def admin_scholarship_delete(
    sid: int,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    row = conn.execute("SELECT name FROM scholarships WHERE id = ?", (sid,)).fetchone()
    if row:
        conn.execute("DELETE FROM scholarships WHERE id = ?", (sid,))
        return redirect("/admin/scholarships", f"“{row['name']}” removed from the catalogue.")
    return redirect("/admin/scholarships", "Scholarship not found.", "error")


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
@router.get("/applications", response_class=HTMLResponse)
def admin_applications(
    request: Request,
    status: str = "",
    q: str = "",
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    sql = APPLICATION_SELECT + " WHERE 1=1"
    params: list = []
    if status:
        sql += " AND a.status = ?"
        params.append(status)
    if q:
        like = f"%{q.strip()}%"
        sql += " AND (a.application_no LIKE ? OR a.full_name LIKE ? OR s.name LIKE ?)"
        params.extend([like, like, like])
    sql += " ORDER BY a.updated_at DESC"
    rows = [enrich_application(r) for r in conn.execute(sql, params).fetchall()]
    counts = {
        r["status"]: r["n"]
        for r in conn.execute("SELECT status, COUNT(*) n FROM applications GROUP BY status").fetchall()
    }
    return render(
        request,
        "admin/applications.html",
        user=user,
        admin_active="applications",
        apps=rows,
        counts=counts,
        status_filter=status,
        q=q,
        status_options=STATUS_OPTIONS,
        stats=application_stats(conn),
    )


@router.post("/applications/{application_id}/status")
def admin_update_status(
    application_id: int,
    status: str = Form(...),
    remarks: str = Form(""),
    next: str = Form("/admin/applications"),
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    row = conn.execute(
        "SELECT application_no FROM applications WHERE id = ?", (application_id,)
    ).fetchone()
    if not row:
        return redirect(next, "Application not found.", "error")
    if status not in config.STATUS_META:
        return redirect(next, "Unknown status.", "error")
    set_status(conn, application_id, status, remarks.strip(), actor=user["full_name"])
    return redirect(
        next,
        f"{row['application_no']} moved to “{config.STATUS_META[status]['label']}”.",
    )


# --------------------------------------------------------------------------- #
# Announcements
# --------------------------------------------------------------------------- #
@router.get("/announcements", response_class=HTMLResponse)
def admin_announcements(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    rows = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM announcements ORDER BY pinned DESC, created_at DESC"
        ).fetchall()
    ]
    return render(
        request, "admin/announcements.html", user=user, admin_active="announcements",
        announcements=rows,
    )


@router.post("/announcements")
def admin_announcement_create(
    title: str = Form(...),
    body: str = Form(...),
    tag: str = Form("General"),
    pinned: str = Form(""),
    link: str = Form(""),
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    if len(title.strip()) < 5 or len(body.strip()) < 10:
        return redirect("/admin/announcements", "Add a longer title and body for the notice.", "error")
    conn.execute(
        "INSERT INTO announcements (title, body, tag, pinned, link) VALUES (?,?,?,?,?)",
        (title.strip(), body.strip(), tag.strip() or "General", 1 if pinned else 0, link.strip() or None),
    )
    return redirect("/admin/announcements", "Notice published.")


@router.post("/announcements/{aid}/toggle")
def admin_announcement_toggle(
    aid: int,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    row = conn.execute("SELECT pinned FROM announcements WHERE id = ?", (aid,)).fetchone()
    if row:
        conn.execute("UPDATE announcements SET pinned = ? WHERE id = ?", (0 if row["pinned"] else 1, aid))
    return redirect("/admin/announcements", "Notice updated.")


@router.post("/announcements/{aid}/delete")
def admin_announcement_delete(
    aid: int,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    conn.execute("DELETE FROM announcements WHERE id = ?", (aid,))
    return redirect("/admin/announcements", "Notice deleted.")


# --------------------------------------------------------------------------- #
# Messages & students
# --------------------------------------------------------------------------- #
@router.get("/messages", response_class=HTMLResponse)
def admin_messages(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    rows = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM contact_messages ORDER BY status = 'new' DESC, created_at DESC"
        ).fetchall()
    ]
    return render(
        request, "admin/messages.html", user=user, admin_active="messages",
        messages=rows,
        new_count=sum(1 for m in rows if m["status"] == "new"),
    )


@router.post("/messages/{mid}/resolve")
def admin_message_resolve(
    mid: int,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    conn.execute("UPDATE contact_messages SET status = 'resolved' WHERE id = ?", (mid,))
    return redirect("/admin/messages", "Message marked as resolved.")


@router.get("/students", response_class=HTMLResponse)
def admin_students(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_admin),
):
    rows = [
        dict(r)
        for r in conn.execute(
            """SELECT u.*, COUNT(a.id) AS apps,
                      SUM(CASE WHEN a.status IN ('approved','disbursed') THEN 1 ELSE 0 END) AS approved
               FROM users u LEFT JOIN applications a ON a.user_id = u.id
               WHERE u.role = 'student'
               GROUP BY u.id ORDER BY u.id DESC"""
        ).fetchall()
    ]
    return render(
        request, "admin/students.html", user=user, admin_active="students", students=rows
    )
