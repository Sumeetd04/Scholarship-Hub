"""Small JSON API, also powering the live search suggestions in the UI."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import db_dependency
from ..security import get_current_user
from ..services import (
    application_events,
    application_stats,
    catalogue_stats,
    get_application_by_no,
    list_scholarships,
    user_applications,
)

router = APIRouter(prefix="/api", tags=["api"])


def _card(s: dict) -> dict:
    return {
        "id": s["id"],
        "slug": s["slug"],
        "name": s["name"],
        "provider": s["provider"],
        "category": s["category"],
        "level": s["level"],
        "state": s["state"],
        "amount": s["amount"],
        "amount_value": s["amount_value"],
        "deadline": s["deadline"],
        "deadline_label": s["deadline_label"],
        "urgency": s["urgency"],
        "official_link": s["official_link"],
        "tags": s["tags_list"],
    }


@router.get("/scholarships")
def api_scholarships(
    q: str = "",
    category: str = "",
    state: str = "",
    level: str = "",
    limit: int = Query(10, ge=1, le=50),
    conn: sqlite3.Connection = Depends(db_dependency),
):
    results = list_scholarships(
        conn, q=q, category=category, state=state, level=level, sort="deadline", limit=limit
    )
    return {"count": len(results), "results": [_card(s) for s in results]}


@router.get("/scholarships/{slug}")
def api_scholarship(slug: str, conn: sqlite3.Connection = Depends(db_dependency)):
    from ..services import get_scholarship

    sch = get_scholarship(conn, slug)
    if not sch:
        raise HTTPException(status_code=404, detail="Scholarship not found")
    return {**_card(sch), "description": sch["description"], "eligibility": sch["eligibility"],
            "benefits": sch["benefits"], "documents": sch["documents"]}


@router.get("/stats")
def api_stats(conn: sqlite3.Connection = Depends(db_dependency)):
    return catalogue_stats(conn)


@router.get("/track/{app_no}")
def api_track(
    app_no: str,
    dob: str = "",
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    app = get_application_by_no(conn, app_no)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    allowed = bool(
        (user and (user["id"] == app["user_id"] or user["role"] == "admin"))
        or (dob and app.get("dob") and dob == app["dob"])
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Date of birth is required to view this application")
    return {
        "application_no": app["application_no"],
        "scholarship": app["scholarship_name"],
        "status": app["status"],
        "status_label": app["status_meta"]["label"],
        "progress": app["progress"],
        "updated_at": app["updated_at"],
        "timeline": [
            {"status": e["status"], "title": e["title"], "note": e["note"], "at": e["created_at"]}
            for e in application_events(conn, app["id"])
        ],
    }


@router.get("/me")
def api_me(
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Sign in required")
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "otr": user["otr"],
        "role": user["role"],
        "stats": application_stats(conn, user["id"]),
        "applications": [
            {
                "application_no": a["application_no"],
                "scholarship": a["scholarship_name"],
                "status": a["status"],
                "progress": a["progress"],
            }
            for a in user_applications(conn, user["id"])
        ],
    }
