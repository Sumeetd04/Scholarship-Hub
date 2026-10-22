"""Jinja2 setup: shared globals, filters and the render helper."""
from __future__ import annotations

import json
from datetime import date
from typing import Any, Optional

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import config
from .services import (
    datetime_label,
    deadline_label,
    humanise_date,
    inr,
    relative_time,
    short_amount,
    urgency,
)

templates = Jinja2Templates(directory=str(config.APP_DIR / "templates"))


def _initials(name: str | None) -> str:
    if not name:
        return "SH"
    parts = [p for p in name.replace(".", " ").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "SH"


def _split_lines(value: str | None) -> list[str]:
    return [line.strip() for line in (value or "").split("\n") if line.strip()]


def _plain_lines(value: str | None) -> list[str]:
    return [line.lstrip("• ").strip() for line in (value or "").split("\n") if line.strip()]


templates.env.filters.update(
    {
        "inr": inr,
        "short_amount": short_amount,
        "date_human": humanise_date,
        "datetime_human": datetime_label,
        "relative": relative_time,
        "deadline_label": deadline_label,
        "urgency": urgency,
        "initials": _initials,
        "lines": _split_lines,
        "plain_lines": _plain_lines,
    }
)

templates.env.globals.update(
    {
        "APP_NAME": config.APP_NAME,
        "APP_TAGLINE": config.APP_TAGLINE,
        "SUPPORT_EMAIL": config.SUPPORT_EMAIL,
        "STATUS_META": config.STATUS_META,
        "STATUS_FLOW": config.STATUS_FLOW,
        "CATEGORIES": config.CATEGORIES,
        "LEVELS": config.LEVELS,
        "STATES": config.STATES,
        "SOCIAL_CATEGORIES": config.SOCIAL_CATEGORIES,
        "GENDERS": config.GENDERS,
        "CURRENT_YEAR": date.today().year,
        "TODAY": date.today().isoformat(),
    }
)


def flash_cookie(message: str, kind: str = "success") -> str:
    return json.dumps({"message": message, "kind": kind})


def redirect(url: str, message: str | None = None, kind: str = "success") -> RedirectResponse:
    response = RedirectResponse(url=url, status_code=303)
    if message:
        response.set_cookie(
            "sh_flash", flash_cookie(message, kind), max_age=30, httponly=True, samesite="lax"
        )
    return response


def render(
    request: Request,
    template: str,
    *,
    user: Optional[Any] = None,
    status_code: int = 200,
    **context: Any,
) -> HTMLResponse:
    flash = getattr(request.state, "flash", None)
    ctx = {
        "request": request,
        "current_user": user or getattr(request.state, "user", None),
        "flash": flash,
        "path": request.url.path,
        "query": dict(request.query_params),
    }
    ctx.update(context)
    return templates.TemplateResponse(request, template, ctx, status_code=status_code)
