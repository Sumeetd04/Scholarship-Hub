"""Catalogue browsing, detail pages, state directory and the match finder."""
from __future__ import annotations

import sqlite3
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import config
from ..database import db_dependency
from ..security import get_current_user
from ..services import (
    applied_scholarship_ids,
    catalogue_stats,
    category_counts,
    decorate_scholarship,
    get_scholarship,
    list_scholarships,
    match_score,
    related_scholarships,
    saved_ids,
)
from ..templating import render

router = APIRouter()
PAGE_SIZE = 9


def _page_window(page: int, pages: int) -> list[int | None]:
    """Page numbers to render, with None marking an ellipsis."""
    if pages <= 7:
        return list(range(1, pages + 1))
    wanted = {1, pages, page - 1, page, page + 1}
    if page <= 3:
        wanted |= {2, 3, 4}
    if page >= pages - 2:
        wanted |= {pages - 1, pages - 2, pages - 3}
    out: list[int | None] = []
    previous = 0
    for p in sorted(x for x in wanted if 1 <= x <= pages):
        if previous and p - previous > 1:
            out.append(None)
        out.append(p)
        previous = p
    return out


@router.get("/scholarships", response_class=HTMLResponse, name="scholarships_list")
def scholarship_list(
    request: Request,
    q: str = "",
    category: str = "",
    state: str = "",
    level: str = "",
    sort: str = "deadline",
    page: int = 1,
    show: str = "open",
    gender: str = "",
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    include_closed = show == "all"
    matches = list_scholarships(
        conn,
        q=q,
        category=category,
        state=state,
        level=level,
        sort=sort if sort in {"deadline", "amount", "newest", "az"} else "deadline",
        include_closed=include_closed,
        gender=gender,
    )
    total = len(matches)
    page = max(1, page)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, pages)
    items = matches[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    # Sidebar counts (unfiltered, so users can always see the catalogue shape)
    cat_counts = {
        r["category"]: r["n"]
        for r in conn.execute(
            "SELECT category, COUNT(*) n FROM scholarships GROUP BY category"
        ).fetchall()
    }
    level_counts = {
        r["level"]: r["n"]
        for r in conn.execute(
            "SELECT level, COUNT(*) n FROM scholarships GROUP BY level ORDER BY n DESC"
        ).fetchall()
    }
    state_counts = [
        dict(r)
        for r in conn.execute(
            """SELECT state, COUNT(*) n FROM scholarships
               WHERE state != 'All India' GROUP BY state ORDER BY n DESC, state ASC LIMIT 14"""
        ).fetchall()
    ]

    filters = {"q": q, "category": category, "state": state, "level": level,
               "sort": sort, "show": show, "gender": gender}
    all_states = sorted({r["state"] for r in conn.execute(
        "SELECT DISTINCT state FROM scholarships WHERE state != 'All India'").fetchall()})

    return render(
        request,
        "scholarships.html",
        user=user,
        scholarships=items,
        total=total,
        page=page,
        pages=pages,
        page_items=_page_window(page, pages),
        page_size=PAGE_SIZE,
        filters=filters,
        cat_counts=cat_counts,
        level_counts=level_counts,
        state_counts=state_counts,
        all_states=all_states,
        saved_ids=saved_ids(conn, user["id"] if user else None),
        applied_ids=applied_scholarship_ids(conn, user["id"] if user else None),
        stats=catalogue_stats(conn),
    )


@router.get("/scholarships/{slug}", response_class=HTMLResponse)
def scholarship_detail(
    request: Request,
    slug: str,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    sch = get_scholarship(conn, slug)
    if not sch:
        return render(
            request,
            "error.html",
            user=user,
            status_code=404,
            code=404,
            title="Scholarship not found",
            message="This scheme is not in our catalogue. Browse all scholarships to find a match.",
        )

    application = None
    is_saved = False
    score = None
    reasons: list[str] = []
    if user:
        application = conn.execute(
            "SELECT * FROM applications WHERE user_id = ? AND scholarship_id = ?",
            (user["id"], sch["id"]),
        ).fetchone()
        is_saved = bool(
            conn.execute(
                "SELECT 1 FROM saved_scholarships WHERE user_id = ? AND scholarship_id = ?",
                (user["id"], sch["id"]),
            ).fetchone()
        )
        profile = dict(user)
        score, reasons = match_score(profile, sch)
    else:
        score, reasons = match_score({}, sch)

    return render(
        request,
        "scholarship_detail.html",
        user=user,
        sch=sch,
        related=related_scholarships(conn, sch, limit=3),
        application=application,
        is_saved=is_saved,
        score=score,
        reasons=reasons,
        saved_ids={sch["id"]} if is_saved else set(),
    )


@router.get("/states", response_class=HTMLResponse)
def states_directory(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    rows = [
        dict(r)
        for r in conn.execute(
            """SELECT state, COUNT(*) n, MAX(amount_value) top
               FROM scholarships WHERE state != 'All India'
               GROUP BY state ORDER BY state ASC"""
        ).fetchall()
    ]
    all_india = conn.execute(
        "SELECT COUNT(*) n FROM scholarships WHERE state = 'All India'"
    ).fetchone()["n"]
    return render(
        request,
        "states.html",
        user=user,
        states=rows,
        all_india=all_india,
        stats=catalogue_stats(conn),
    )


@router.get("/states/{state}", response_class=HTMLResponse)
def state_scholarships(state: str):
    return RedirectResponse(f"/scholarships?state={quote(state)}", status_code=307)


@router.get("/finder", response_class=HTMLResponse)
def finder(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
    state: str = "",
    level: str = "",
    category: str = "",
    gender: str = "",
    income: str = "",
    disability: str = "",
    minority: str = "",
):
    provided = any([state, level, category, gender, income, disability, minority])
    profile = {
        "state": state,
        "level": level,
        "category": category,
        "gender": gender,
        "annual_income": int(income) if income.isdigit() else 0,
        "disability": disability == "1",
        "minority": minority == "1",
    }

    results, low_confidence = [], True
    if provided:
        pool = list_scholarships(conn, sort="deadline", include_closed=False)
        scored = []
        for s in pool:
            score, reasons = match_score(profile, s)
            scored.append((score, reasons, s))
        scored.sort(key=lambda x: (-x[0], x[2]["deadline"]))
        results = [
            {**s, "score": sc, "reasons": rs}
            for sc, rs, s in scored
            if sc >= 40
        ][:18]
        low_confidence = len(results) < 4

    return render(
        request,
        "finder.html",
        user=user,
        results=results,
        profile=profile,
        provided=provided,
        low_confidence=low_confidence,
        total_open=len(list_scholarships(conn, include_closed=False)),
        saved_ids=saved_ids(conn, user["id"] if user else None),
    )
