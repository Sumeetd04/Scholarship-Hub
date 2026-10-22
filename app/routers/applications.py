"""Student area: dashboard, applications, saved schemes and profile."""
from __future__ import annotations

import re
import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import config
from ..database import db_dependency
from ..security import get_current_user, hash_password, require_user, verify_password
from ..services import (
    application_stats,
    applied_scholarship_ids,
    create_application,
    get_scholarship,
    list_scholarships,
    match_score,
    saved_ids,
    saved_scholarships,
    user_applications,
)
from ..templating import redirect, render

router = APIRouter()

PROFILE_FIELDS = [
    "full_name", "email", "phone", "dob", "gender", "category",
    "annual_income", "state", "institute", "course", "level",
]


def _safe_next(value: str | None, fallback: str = "/dashboard") -> str:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return fallback


def _completeness(user: sqlite3.Row) -> tuple[int, list[str]]:
    filled = [f for f in PROFILE_FIELDS if user[f] not in (None, "", 0)]
    missing = [f for f in PROFILE_FIELDS if f not in filled]
    return round(len(filled) / len(PROFILE_FIELDS) * 100), missing


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    welcome: int = 0,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    apps = user_applications(conn, user["id"])
    stats = application_stats(conn, user["id"])
    saved = saved_scholarships(conn, user["id"])[:4]
    applied = applied_scholarship_ids(conn, user["id"])
    profile_pct, missing = _completeness(user)

    pool = list_scholarships(conn, sort="deadline", include_closed=False)
    scored = []
    for s in pool:
        if s["id"] in applied:
            continue
        score, reasons = match_score(dict(user), s)
        scored.append((score, reasons, s))
    scored.sort(key=lambda x: (-x[0], x[2]["deadline"]))
    recommended = [{**s, "score": sc, "reasons": rs} for sc, rs, s in scored[:4]]

    upcoming = sorted(
        [a for a in apps if a["status"] in {"submitted", "under_review", "documents_verified", "on_hold"}],
        key=lambda a: a["deadline"] or "9999",
    )[:3]

    return render(
        request,
        "dashboard.html",
        user=user,
        apps=apps,
        stats=stats,
        saved=saved,
        recommended=recommended,
        profile_pct=profile_pct,
        missing=missing,
        upcoming=upcoming,
        welcome=welcome,
        saved_ids=saved_ids(conn, user["id"]),
    )


@router.get("/dashboard/saved", response_class=HTMLResponse)
def saved_page(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    items = saved_scholarships(conn, user["id"])
    return render(
        request,
        "saved.html",
        user=user,
        scholarships=items,
        saved_ids={s["id"] for s in items},
        applied_ids=applied_scholarship_ids(conn, user["id"]),
    )


@router.post("/saved/{slug}/toggle")
def toggle_saved(
    slug: str,
    next: str = Form("/scholarships"),
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    sch = get_scholarship(conn, slug)
    if not sch:
        return redirect("/scholarships", "That scholarship could not be found.", "error")
    existing = conn.execute(
        "SELECT id FROM saved_scholarships WHERE user_id = ? AND scholarship_id = ?",
        (user["id"], sch["id"]),
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM saved_scholarships WHERE id = ?", (existing["id"],))
        message = f"Removed “{sch['name']}” from your saved list."
    else:
        conn.execute(
            "INSERT INTO saved_scholarships (user_id, scholarship_id) VALUES (?,?)",
            (user["id"], sch["id"]),
        )
        message = f"Saved “{sch['name']}”. We will keep its deadline in view."
    return redirect(_safe_next(next, f"/scholarships/{slug}"), message)


@router.get("/apply/{slug}", response_class=HTMLResponse)
def apply_page(
    request: Request,
    slug: str,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    sch = get_scholarship(conn, slug)
    if not sch:
        return redirect("/scholarships", "That scholarship could not be found.", "error")

    existing = conn.execute(
        "SELECT application_no FROM applications WHERE user_id = ? AND scholarship_id = ?",
        (user["id"], sch["id"]),
    ).fetchone()
    if existing:
        return redirect(
            f"/track/{existing['application_no']}",
            "You have already applied for this scholarship. Here is your live status.",
        )
    if sch["days_left"] < 0:
        return redirect(f"/scholarships/{slug}", "Applications for this scheme are closed for the current cycle.", "error")

    return render(
        request, "apply.html", user=user, sch=sch, form=dict(user), error=None
    )


@router.post("/apply/{slug}", response_class=HTMLResponse)
def apply_submit(
    request: Request,
    slug: str,
    full_name: str = Form(...),
    dob: str = Form(""),
    gender: str = Form(""),
    category: str = Form(""),
    annual_income: str = Form("0"),
    state: str = Form(""),
    institute: str = Form(""),
    course: str = Form(""),
    level: str = Form(""),
    note: str = Form(""),
    consent: str = Form(""),
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    sch = get_scholarship(conn, slug)
    if not sch:
        return redirect("/scholarships", "That scholarship could not be found.", "error")

    blockers = []
    full_name = " ".join(full_name.split())
    if len(full_name) < 3:
        blockers.append("Enter your full name as printed on your documents.")
    if not dob:
        blockers.append("Date of birth is required.")
    if not state:
        blockers.append("Select your state of domicile.")
    if not institute.strip():
        blockers.append("Enter your current institute or school.")
    if not consent:
        blockers.append("You must confirm that the information provided is accurate.")

    try:
        income = max(0, int(re.sub(r"[^\d]", "", annual_income) or 0))
    except ValueError:
        income = 0

    if blockers:
        return render(
            request,
            "apply.html",
            user=user,
            sch=sch,
            status_code=422,
            error=" ".join(blockers),
            form={
                "full_name": full_name, "dob": dob, "gender": gender, "category": category,
                "annual_income": income, "state": state, "institute": institute,
                "course": course, "level": level, "note": note,
            },
        )

    payload = {
        "full_name": full_name, "dob": dob, "gender": gender, "category": category,
        "annual_income": income, "state": state, "institute": institute,
        "course": course, "level": level, "note": note,
    }
    try:
        result = create_application(conn, user, sch, payload)
    except sqlite3.IntegrityError:
        return redirect("/dashboard", "You have already applied for this scholarship.", "error")

    return redirect(
        f"/track/{result['application_no']}?new=1",
        "Application submitted. Your submission ID is ready — save it.",
    )


@router.post("/applications/{application_id}/withdraw")
def withdraw_application(
    application_id: int,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    row = conn.execute(
        "SELECT * FROM applications WHERE id = ? AND user_id = ?",
        (application_id, user["id"]),
    ).fetchone()
    if not row:
        return redirect("/dashboard", "Application not found.", "error")
    if row["status"] not in {"submitted", "under_review", "on_hold"}:
        return redirect("/dashboard", "This application can no longer be withdrawn.", "error")

    from ..services import set_status

    set_status(conn, application_id, "withdrawn", "Withdrawn by the student from the dashboard.", actor="student")
    return redirect("/dashboard", "Application withdrawn. You can apply again if the window is open.")


@router.get("/profile", response_class=HTMLResponse)
def profile_page(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    pct, missing = _completeness(user)
    return render(
        request, "profile.html", user=user, profile_pct=pct, missing=missing, error=None, ok=None
    )


@router.post("/profile", response_class=HTMLResponse)
def profile_submit(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(""),
    dob: str = Form(""),
    gender: str = Form(""),
    category: str = Form(""),
    annual_income: str = Form("0"),
    state: str = Form(""),
    institute: str = Form(""),
    course: str = Form(""),
    level: str = Form(""),
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    full_name = " ".join(full_name.split())
    if len(full_name) < 3:
        pct, missing = _completeness(user)
        return render(
            request, "profile.html", user=user, profile_pct=pct, missing=missing,
            status_code=422, error="Please enter your full name.", ok=None,
        )
    try:
        income = max(0, int(re.sub(r"[^\d]", "", annual_income) or 0))
    except ValueError:
        income = 0

    conn.execute(
        """UPDATE users SET full_name = ?, phone = ?, dob = ?, gender = ?, category = ?,
               annual_income = ?, state = ?, institute = ?, course = ?, level = ?
           WHERE id = ?""",
        (full_name, phone, dob, gender, category, income, state, institute, course, level, user["id"]),
    )
    return redirect("/profile", "Profile updated. Your recommendations are now more accurate.")


@router.post("/profile/password", response_class=HTMLResponse)
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(require_user),
):
    pct, missing = _completeness(user)
    if not verify_password(current_password, user["password_hash"]):
        return render(
            request, "profile.html", user=user, profile_pct=pct, missing=missing,
            status_code=422, error="Your current password is incorrect.", ok=None,
        )
    if len(new_password) < 8:
        return render(
            request, "profile.html", user=user, profile_pct=pct, missing=missing,
            status_code=422, error="Choose a new password of at least 8 characters.", ok=None,
        )
    if new_password != confirm_password:
        return render(
            request, "profile.html", user=user, profile_pct=pct, missing=missing,
            status_code=422, error="The new passwords do not match.", ok=None,
        )
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user["id"])
    )
    return redirect("/profile", "Password updated successfully.")
