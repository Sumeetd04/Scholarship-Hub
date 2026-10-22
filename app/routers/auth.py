"""Sign up, sign in, sign out."""
from __future__ import annotations

import re
import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import config
from ..database import db_dependency
from ..security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..services import generate_otr
from ..templating import redirect, render

router = APIRouter()
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def _safe_next(value: str | None) -> str:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return "/dashboard"


def _sign_in(user_id: int, role: str, url: str) -> RedirectResponse:
    response = redirect(url)
    response.set_cookie(
        key=config.COOKIE_NAME,
        value=create_access_token(user_id, role),
        max_age=config.TOKEN_TTL_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=config.COOKIE_SECURE,
    )
    return response


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request, next: str = "", user=Depends(get_current_user)
):
    if user:
        return redirect("/dashboard")
    return render(request, "login.html", user=None, next=_safe_next(next), email="", error=None)


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/dashboard"),
    conn: sqlite3.Connection = Depends(db_dependency),
):
    email = email.strip().lower()
    row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        return render(
            request,
            "login.html",
            user=None,
            status_code=401,
            next=_safe_next(next),
            email=email,
            error="That email and password combination does not match our records.",
        )

    url = "/admin" if row["role"] == "admin" and next in ("", "/", "/dashboard") else _safe_next(next)
    return _sign_in(row["id"], row["role"], url)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, user=Depends(get_current_user)):
    if user:
        return redirect("/dashboard")
    return render(
        request, "register.html", user=None, form={}, error=None,
        states=config.STATES, categories=config.SOCIAL_CATEGORIES, levels=config.LEVELS,
    )


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
    state: str = Form(""),
    category: str = Form("General"),
    level: str = Form("Undergraduate"),
    annual_income: str = Form("0"),
    consent: str = Form(""),
    conn: sqlite3.Connection = Depends(db_dependency),
):
    full_name = " ".join(full_name.split())
    email = email.strip().lower()
    phone = phone.strip()
    errors = []

    if len(full_name) < 3:
        errors.append("Enter your full name as it appears on your documents.")
    if not EMAIL_RE.match(email):
        errors.append("Enter a valid email address.")
    if phone and (len(re.sub(r"\D", "", phone)) != 10 and len(re.sub(r"\D", "", phone)) != 12):
        errors.append("Enter a 10-digit Indian mobile number.")
    if len(password) < 8:
        errors.append("Use a password of at least 8 characters.")
    if password != confirm_password:
        errors.append("The two passwords do not match.")
    if not consent:
        errors.append("Please accept the data-use consent to continue.")
    if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
        errors.append("An account with this email already exists. Try signing in instead.")

    try:
        income = max(0, int(re.sub(r"[^\d]", "", annual_income) or 0))
    except ValueError:
        income = 0

    if errors:
        return render(
            request,
            "register.html",
            user=None,
            status_code=422,
            error=" ".join(errors),
            form={
                "full_name": full_name, "email": email, "phone": phone,
                "state": state, "category": category, "level": level,
                "annual_income": income,
            },
            states=config.STATES,
            categories=config.SOCIAL_CATEGORIES,
            levels=config.LEVELS,
        )

    cur = conn.execute(
        """INSERT INTO users (full_name, email, phone, password_hash, role, otr,
                              category, annual_income, state, level)
           VALUES (?,?,?,?, 'student', ?,?,?,?,?)""",
        (
            full_name, email, phone, hash_password(password), generate_otr(),
            category, income, state or "All India", level,
        ),
    )
    response = _sign_in(cur.lastrowid, "student", "/dashboard?welcome=1")
    return response


@router.post("/logout")
def logout():
    response = redirect("/", "You have signed out. See you soon!")
    response.delete_cookie(config.COOKIE_NAME)
    return response
