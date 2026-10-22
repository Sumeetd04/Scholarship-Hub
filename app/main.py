"""FastAPI application entry point."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from . import config
from .database import init_db
from .routers import admin, api, applications, auth, public, scholarships, tracker
from .templating import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    seeded = init_db()
    if seeded:
        print("✓ Seeded scholarship catalogue and demo data")
    print(f"✓ Scholarship Hub ready on {config.DB_PATH}")
    yield


app = FastAPI(
    title="Scholarship Hub API",
    description="Discover Indian scholarships and track every application in one place.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(GZipMiddleware, minimum_size=800)
app.mount("/static", StaticFiles(directory=str(config.APP_DIR / "static")), name="static")


@app.middleware("http")
async def flash_and_headers(request: Request, call_next):
    """Expose the one-shot flash cookie to templates, then clear it.

    A response that sets a *new* flash cookie (the redirect after a form post)
    must keep it, so deletion is skipped in that case.
    """
    raw = request.cookies.get("sh_flash")
    if raw:
        try:
            request.state.flash = json.loads(raw)
        except (ValueError, TypeError):
            request.state.flash = None

    response = await call_next(request)

    set_cookies = [v for k, v in response.raw_headers if k.lower() == b"set-cookie"]
    sets_new_flash = any(b"sh_flash=" in c and b"Max-Age=0" not in c for c in set_cookies)
    if raw and not sets_new_flash:
        response.delete_cookie("sh_flash")

    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": exc.detail}, status_code=401)
        target = request.url.path
        if request.url.query:
            target += "?" + request.url.query
        url = "/login"
        if target not in ("/login", "/"):
            from urllib.parse import quote

            url += "?next=" + quote(target)
        return RedirectResponse(url, status_code=303)

    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    message = {
        403: "You do not have permission to open this page.",
        404: "We could not find that page.",
    }.get(exc.status_code, str(exc.detail))
    return render(
        request,
        "error.html",
        status_code=exc.status_code,
        code=exc.status_code,
        title="Access restricted" if exc.status_code == 403 else "Not found",
        message=message,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import logging

    logging.getLogger("scholarship_hub").exception("Unhandled error on %s", request.url.path)
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
    return render(
        request,
        "error.html",
        status_code=500,
        code=500,
        title="Something went wrong",
        message="Our side dropped the ball. Please retry in a moment — your applications are safe.",
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    return render(
        request,
        "error.html",
        status_code=404,
        code=404,
        title="Page not found",
        message="The page you are looking for has moved or never existed.",
    )


app.include_router(public.router)
app.include_router(auth.router)
app.include_router(scholarships.router)
app.include_router(applications.router)
app.include_router(tracker.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "app": config.APP_NAME, "version": "2.0.0"}
