"""Home page, static/informational pages and the contact form."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from .. import config
from ..database import db_dependency
from ..security import get_current_user
from ..services import (
    catalogue_stats,
    category_counts,
    list_scholarships,
    saved_ids,
    state_counts,
)
from ..templating import redirect, render

router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="home")
def home(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    stats = catalogue_stats(conn)
    featured = list_scholarships(
        conn, sort="deadline", include_closed=False, limit=6, featured_only=True
    )
    if len(featured) < 6:
        seen = {s["id"] for s in featured}
        for s in list_scholarships(conn, sort="deadline", include_closed=False, limit=12):
            if s["id"] not in seen:
                featured.append(s)
                seen.add(s["id"])
            if len(featured) >= 6:
                break

    closing = list_scholarships(conn, sort="deadline", include_closed=False, limit=4)
    categories = category_counts(conn)
    states = state_counts(conn, limit=12)
    announcements = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM announcements ORDER BY pinned DESC, created_at DESC LIMIT 3"
        ).fetchall()
    ]
    saved = saved_ids(conn, user["id"] if user else None)
    demo_row = conn.execute(
        "SELECT application_no, dob FROM applications WHERE dob IS NOT NULL ORDER BY id LIMIT 1"
    ).fetchone()

    return render(
        request,
        "home.html",
        user=user,
        stats=stats,
        demo=dict(demo_row) if demo_row else None,
        featured=featured,
        closing=closing,
        categories=categories,
        states=states,
        announcements=announcements,
        saved_ids=saved,
        page="home",
    )


@router.get("/about", response_class=HTMLResponse)
def about(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    return render(request, "about.html", user=user, stats=catalogue_stats(conn))


@router.get("/faq", response_class=HTMLResponse)
def faq(request: Request, user=Depends(get_current_user)):
    return render(request, "faq.html", user=user)


@router.get("/contact", response_class=HTMLResponse)
def contact_page(request: Request, user=Depends(get_current_user)):
    return render(request, "contact.html", user=user, form={}, error=None)


@router.post("/contact", response_class=HTMLResponse)
def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(""),
    message: str = Form(...),
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    name, email, message = name.strip(), email.strip(), message.strip()
    errors = []
    if len(name) < 2:
        errors.append("Please tell us your name.")
    if "@" not in email or "." not in email.split("@")[-1]:
        errors.append("Please enter a valid email address.")
    if len(message) < 10:
        errors.append("Please add a little more detail (at least 10 characters).")

    if errors:
        return render(
            request,
            "contact.html",
            user=user,
            status_code=422,
            form={"name": name, "email": email, "subject": subject, "message": message},
            error=" ".join(errors),
        )

    conn.execute(
        "INSERT INTO contact_messages (name, email, subject, message) VALUES (?,?,?,?)",
        (name, email, subject.strip(), message),
    )
    return redirect(
        "/contact",
        "Message received. Our student support team replies within one working day.",
    )


@router.get("/announcements", response_class=HTMLResponse)
def announcements(
    request: Request,
    tag: str = "",
    conn: sqlite3.Connection = Depends(db_dependency),
    user=Depends(get_current_user),
):
    if tag:
        rows = conn.execute(
            "SELECT * FROM announcements WHERE tag = ? ORDER BY pinned DESC, created_at DESC",
            (tag,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM announcements ORDER BY pinned DESC, created_at DESC"
        ).fetchall()
    tags = [
        r["tag"]
        for r in conn.execute(
            "SELECT DISTINCT tag FROM announcements ORDER BY tag ASC"
        ).fetchall()
    ]
    return render(
        request,
        "announcements.html",
        user=user,
        announcements=[dict(r) for r in rows],
        tags=tags,
        active_tag=tag,
    )


@router.get("/how-it-works", response_class=HTMLResponse)
def how_it_works(request: Request, user=Depends(get_current_user)):
    return render(request, "how_it_works.html", user=user, support_email=config.SUPPORT_EMAIL)


@router.get("/robots.txt", include_in_schema=False)
def robots(request: Request):
    from fastapi.responses import PlainTextResponse

    base = str(request.base_url).rstrip("/")
    return PlainTextResponse(
        f"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api\nSitemap: {base}/sitemap.xml\n"
    )


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(
    request: Request,
    conn: sqlite3.Connection = Depends(db_dependency),
):
    from fastapi.responses import Response

    base = str(request.base_url).rstrip("/")
    static_pages = [
        "/", "/scholarships", "/states", "/finder", "/track",
        "/announcements", "/faq", "/about", "/contact", "/how-it-works",
    ]
    urls = [f"{base}{p}" for p in static_pages]
    urls += [f"{base}/scholarships/{row['slug']}" for row in conn.execute(
        "SELECT slug FROM scholarships ORDER BY id"
    ).fetchall()]
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        body.append(f"<url><loc>{u}</loc><changefreq>weekly</changefreq></url>")
    body.append("</urlset>")
    return Response("\n".join(body), media_type="application/xml")
