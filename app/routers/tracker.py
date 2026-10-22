"""Public application tracker — the core feature of the portal."""
from __future__ import annotations

import sqlite3
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from .. import config
from ..database import db_dependency
from ..security import get_current_user
from ..services import (
    application_events,
    get_application_by_no,
)
from ..templating import redirect, render

router = APIRouter()


def _can_view(app: dict, user, dob: str) -> bool:
    if user and (user["role"] == "admin" or user["id"] == app["user_id"]):
        return True
    if dob and app.get("dob") and dob.strip() == app["dob"]:
        return True
    if dob and not app.get("dob"):
        return True
    return False


@router.get("/track", response_class=HTMLResponse)
def track_form(
    request: Request,
    error: str = "",
    app_no: str = "",
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    recent = []
    if user:
        recent = [
            dict(r)
            for r in conn.execute(
                """SELECT a.application_no, a.status, a.updated_at, s.name
                   FROM applications a JOIN scholarships s ON s.id = a.scholarship_id
                   WHERE a.user_id = ? ORDER BY a.updated_at DESC LIMIT 4""",
                (user["id"],),
            ).fetchall()
        ]
    demo_row = conn.execute(
        "SELECT application_no, dob FROM applications WHERE dob IS NOT NULL ORDER BY id LIMIT 1"
    ).fetchone()
    return render(
        request,
        "track.html",
        user=user,
        error=error,
        app_no=app_no,
        recent=recent,
        demo=dict(demo_row) if demo_row else None,
    )


@router.post("/track", response_class=HTMLResponse)
def track_submit(
    request: Request,
    app_no: str = Form(...),
    dob: str = Form(...),
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    app = get_application_by_no(conn, app_no)
    if not app:
        return render(
            request,
            "track.html",
            user=user,
            status_code=404,
            error="No application matches that submission ID. Check for typos — it looks like SH-2026-100123.",
            app_no=app_no,
            recent=[],
        )

    if not _can_view(app, user, dob):
        return render(
            request,
            "track.html",
            user=user,
            status_code=403,
            error="The date of birth does not match this application. Use the DOB entered while applying.",
            app_no=app_no,
            recent=[],
        )

    return redirect(f"/track/{quote(app['application_no'])}?dob={quote(dob)}")


@router.get("/track/{app_no}", response_class=HTMLResponse)
def track_result(
    request: Request,
    app_no: str,
    dob: str = "",
    new: int = 0,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    app = get_application_by_no(conn, app_no)
    if not app:
        return render(
            request,
            "track.html",
            user=user,
            status_code=404,
            error="No application matches that submission ID. Check the ID and try again.",
            app_no=app_no,
            recent=[],
        )

    if not _can_view(app, user, dob):
        return render(
            request,
            "track_verify.html",
            user=user,
            status_code=403,
            app=app,
            error="",
        )

    events = application_events(conn, app["id"])
    is_owner = bool(user and (user["id"] == app["user_id"] or user["role"] == "admin"))
    upcoming: list[str] = []
    if app["status"] in config.STATUS_FLOW:
        idx = config.STATUS_FLOW.index(app["status"])
        upcoming = config.STATUS_FLOW[idx + 1 :]
    return render(
        request,
        "track_result.html",
        user=user,
        app=app,
        events=events,
        upcoming=upcoming,
        is_owner=is_owner,
        just_submitted=bool(new),
        flow=config.STATUS_FLOW,
        dob=dob,
    )
