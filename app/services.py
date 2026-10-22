"""Domain logic: catalogue queries, matching, applications and tracking."""
from __future__ import annotations

import math
import secrets
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from . import config

IST = timezone(timedelta(hours=5, minutes=30))


def to_ist(value: datetime) -> datetime:
    """Normalise any stored timestamp to India Standard Time for display."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(IST)

# --------------------------------------------------------------------------- #
# Dates & formatting
# --------------------------------------------------------------------------- #
def parse_date(value: str | None) -> Optional[date]:
    if not value:
        return None
    try:
        return to_ist(datetime.fromisoformat(value.replace("Z", "+00:00"))).date()
    except ValueError:
        return None


def datetime_label(value: str | None) -> str:
    """e.g. 22 Oct 2026 · 11:24 AM (IST)."""
    if not value:
        return ""
    try:
        return to_ist(datetime.fromisoformat(value.replace("Z", "+00:00"))).strftime("%d %b %Y · %I:%M %p")
    except ValueError:
        return ""


def days_left(deadline: str | None, today: Optional[date] = None) -> int:
    d = parse_date(deadline)
    if not d:
        return 9999
    return (d - (today or date.today())).days


def deadline_label(deadline: str | None) -> str:
    """Human friendly deadline text used across cards and detail pages."""
    d = parse_date(deadline)
    if not d:
        return "Rolling"
    left = (d - date.today()).days
    if left < 0:
        return "Closed for this cycle"
    if left == 0:
        return "Closes today"
    if left == 1:
        return "Closes tomorrow"
    if left <= 14:
        return f"Closes in {left} days"
    return d.strftime("%d %b %Y")


def urgency(deadline: str | None) -> str:
    left = days_left(deadline)
    if left < 0:
        return "closed"
    if left <= 10:
        return "urgent"
    if left <= 30:
        return "soon"
    return "open"


def inr(value: int | float | None) -> str:
    """Indian numbering: 12,50,000."""
    if not value:
        return "₹0"
    value = int(value)
    s = str(abs(value))
    if len(s) <= 3:
        body = s
    else:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        body = ",".join(parts) + "," + tail
    return ("-" if value < 0 else "") + "₹" + body


def short_amount(value: int | float | None) -> str:
    if not value:
        return "—"
    value = int(value)
    if value >= 10000000:
        return f"₹{value / 10000000:.1f} Cr"
    if value >= 100000:
        return f"₹{value / 100000:.1f} L"
    if value >= 1000:
        return f"₹{value / 1000:.0f}k"
    return f"₹{value}"


def humanise_date(value: str | None) -> str:
    d = parse_date(value)
    return d.strftime("%d %b %Y") if d else "—"


def relative_time(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600} h ago"
    if seconds < 86400 * 30:
        return f"{seconds // 86400} d ago"
    return dt.strftime("%d %b %Y")


# --------------------------------------------------------------------------- #
# Catalogue
# --------------------------------------------------------------------------- #
SORTS = {
    "deadline": "deadline ASC",
    "amount": "amount_value DESC",
    "newest": "id DESC",
    "az": "name ASC",
}

CATEGORY_VALUES = [
    "Central Government",
    "State Government",
    "Private & Corporate",
    "Trust & Foundation",
]


def _rows(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]


def list_scholarships(
    conn: sqlite3.Connection,
    *,
    q: str = "",
    category: str = "",
    state: str = "",
    level: str = "",
    sort: str = "deadline",
    include_closed: bool = True,
    limit: Optional[int] = None,
    offset: int = 0,
    featured_only: bool = False,
    gender: str = "",
    disability: bool = False,
    minority: bool = False,
    max_income: int | None = None,
) -> list[dict]:
    clauses, params = [], []
    if q:
        like = f"%{q.strip()}%"
        clauses.append(
            "(name LIKE ? OR provider LIKE ? OR description LIKE ? OR tags LIKE ? OR state LIKE ?)"
        )
        params.extend([like] * 5)
    if category:
        clauses.append("category = ?")
        params.append(category)
    if state:
        clauses.append("(state = ? OR state = 'All India')")
        params.append(state)
    if level:
        clauses.append("(level = ? OR level = 'Multiple Levels')")
        params.append(level)
    if featured_only:
        clauses.append("featured = 1")
    if gender:
        clauses.append("(gender = 'Any' OR gender = ?)")
        params.append(gender)
    if disability:
        clauses.append("disability = 1")
    if minority:
        clauses.append("minority = 1")
    if max_income:
        clauses.append("(income_limit = 0 OR income_limit >= ?)")
        params.append(max_income)
    if not include_closed:
        clauses.append("deadline >= date('now')")

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    order = SORTS.get(sort, SORTS["deadline"])
    sql = f"SELECT * FROM scholarships {where} ORDER BY featured DESC, {order}"
    if limit:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    rows = _rows(conn, sql, params)
    for row in rows:
        decorate_scholarship(row)
    return rows


def count_scholarships(conn: sqlite3.Connection, **filters) -> int:
    return len(list_scholarships(conn, **filters))


def decorate_scholarship(row: dict) -> dict:
    row["deadline_label"] = deadline_label(row.get("deadline"))
    row["days_left"] = days_left(row.get("deadline"))
    row["urgency"] = urgency(row.get("deadline"))
    row["tags_list"] = [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()]
    row["eligibility_list"] = [x for x in (row.get("eligibility") or "").split("\n") if x.strip()]
    row["benefits_list"] = [x for x in (row.get("benefits") or "").split("\n") if x.strip()]
    row["documents_list"] = [x for x in (row.get("documents") or "").split("\n") if x.strip()]
    row["short_amount"] = short_amount(row.get("amount_value"))
    return row


def get_scholarship(conn: sqlite3.Connection, slug: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM scholarships WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return None
    data = dict(row)
    decorate_scholarship(data)
    return data


def get_scholarship_by_id(conn: sqlite3.Connection, sid: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM scholarships WHERE id = ?", (sid,)).fetchone()
    if not row:
        return None
    data = dict(row)
    decorate_scholarship(data)
    return data


def related_scholarships(conn: sqlite3.Connection, sch: dict, limit: int = 3) -> list[dict]:
    rows = _rows(
        conn,
        """SELECT * FROM scholarships
           WHERE id != ? AND (category = ? OR state = ?)
           ORDER BY featured DESC, deadline ASC LIMIT ?""",
        (sch["id"], sch["category"], sch["state"], limit),
    )
    for r in rows:
        decorate_scholarship(r)
    return rows


def catalogue_stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) n FROM scholarships").fetchone()["n"]
    states = conn.execute(
        "SELECT COUNT(DISTINCT state) n FROM scholarships WHERE state != 'All India'"
    ).fetchone()["n"]
    central = conn.execute(
        "SELECT COUNT(*) n FROM scholarships WHERE category = 'Central Government'"
    ).fetchone()["n"]
    private = conn.execute(
        "SELECT COUNT(*) n FROM scholarships WHERE category = 'Private & Corporate'"
    ).fetchone()["n"]
    closing = conn.execute(
        "SELECT COUNT(*) n FROM scholarships WHERE deadline >= date('now') AND deadline <= date('now', '+30 day')"
    ).fetchone()["n"]
    top_award = conn.execute("SELECT MAX(amount_value) n FROM scholarships").fetchone()["n"] or 0
    tracked = conn.execute("SELECT COUNT(*) n FROM applications").fetchone()["n"]
    return {
        "total": total,
        "states": states,
        "central": central,
        "private": private,
        "closing": closing,
        "top_award": top_award,
        "tracked": tracked,
    }


def category_counts(conn: sqlite3.Connection) -> list[dict]:
    out = []
    for cat in config.CATEGORIES:
        n = conn.execute("SELECT COUNT(*) n FROM scholarships WHERE category = ?", (cat["name"],)).fetchone()["n"]
        out.append({**cat, "count": n})
    return out


def state_counts(conn: sqlite3.Connection, limit: int = 12) -> list[dict]:
    rows = _rows(
        conn,
        """SELECT state, COUNT(*) n FROM scholarships
           WHERE state != 'All India' GROUP BY state ORDER BY n DESC, state ASC LIMIT ?""",
        (limit,),
    )
    return rows


# --------------------------------------------------------------------------- #
# Matching engine
# --------------------------------------------------------------------------- #
def match_score(profile: dict, sch: dict) -> tuple[int, list[str]]:
    """Score a scholarship against a student profile (0-100) plus human reasons."""
    score, reasons = 50, []

    s_state = (sch.get("state") or "All India")
    p_state = profile.get("state") or ""
    if s_state == "All India":
        score += 10
        reasons.append("Open to students across India")
    elif p_state and s_state == p_state:
        score += 22
        reasons.append(f"Reserved for {s_state} students")
    else:
        score -= 25

    p_level = profile.get("level") or ""
    if p_level:
        if sch.get("level") == p_level:
            score += 16
            reasons.append(f"Matches your {p_level} study level")
        elif sch.get("level") == "Multiple Levels":
            score += 10
            reasons.append("Covers multiple study levels")
        else:
            score -= 12

    income = int(profile.get("annual_income") or 0)
    limit = int(sch.get("income_limit") or 0)
    if limit:
        if income and income <= limit:
            score += 14
            reasons.append(f"Your income is within the {short_amount(limit)} ceiling")
        elif income:
            score -= 30
    else:
        score += 4

    p_gender = profile.get("gender") or ""
    if (sch.get("gender") or "Any") == "Female":
        if p_gender == "Female":
            score += 14
            reasons.append("Exclusive to girl students")
        else:
            score -= 40

    category = (profile.get("category") or "").upper()
    tags = (sch.get("tags") or "").lower()
    if category in {"SC", "ST", "OBC", "EWS", "DNT"} and category.lower() in tags:
        score += 12
        reasons.append(f"Priority scheme for {category} students")
    if category == "MINORITY" and sch.get("minority"):
        score += 14
        reasons.append("For notified minority communities")
    if profile.get("disability"):
        if sch.get("disability"):
            score += 18
            reasons.append("Reserved for students with disabilities")
        else:
            score += 2

    if sch.get("featured"):
        score += 3
        reasons.append("Featured, high-demand scheme")

    left = days_left(sch.get("deadline"))
    if left < 0:
        score -= 20
    elif left <= 10:
        reasons.append(f"Apply now — {max(0, left)} days left")

    return max(0, min(100, score)), reasons[:5]


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
def generate_application_no(conn: sqlite3.Connection) -> str:
    year = date.today().year
    while True:
        candidate = f"SH-{year}-{secrets.randbelow(900000) + 100000}"
        exists = conn.execute(
            "SELECT 1 FROM applications WHERE application_no = ?", (candidate,)
        ).fetchone()
        if not exists:
            return candidate


def generate_otr() -> str:
    return "OTR" + "".join(secrets.choice("0123456789") for _ in range(10))


def create_application(
    conn: sqlite3.Connection, user: sqlite3.Row, sch: dict, payload: dict
) -> dict:
    app_no = generate_application_no(conn)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    cur = conn.execute(
        """INSERT INTO applications (application_no, user_id, scholarship_id, status, full_name,
               dob, gender, category, annual_income, state, institute, course, level, note,
               remarks, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            app_no, user["id"], sch["id"], "submitted",
            payload.get("full_name") or user["full_name"],
            payload.get("dob") or user["dob"],
            payload.get("gender") or user["gender"],
            payload.get("category") or user["category"],
            int(payload.get("annual_income") or user["annual_income"] or 0),
            payload.get("state") or user["state"],
            payload.get("institute") or user["institute"],
            payload.get("course") or user["course"],
            payload.get("level") or user["level"],
            payload.get("note") or "",
            None, now, now,
        ),
    )
    add_event(conn, cur.lastrowid, "submitted",
              "Application submitted through Scholarship Hub",
              "Your application was received. Keep the submission ID for tracking.", actor="student")
    return {
        "id": cur.lastrowid,
        "application_no": app_no,
        "scholarship": sch,
        "created_at": now,
    }


def add_event(
    conn: sqlite3.Connection,
    application_id: int,
    status: str,
    title: str,
    note: str = "",
    actor: str = "system",
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    conn.execute(
        """INSERT INTO application_events (application_id, status, title, note, actor, created_at)
           VALUES (?,?,?,?,?,?)""",
        (application_id, status, title, note, actor, now),
    )


def set_status(conn: sqlite3.Connection, application_id: int, status: str, remarks: str = "",
               actor: str = "admin") -> None:
    meta = config.STATUS_META.get(status, {"label": status})
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    conn.execute(
        "UPDATE applications SET status = ?, remarks = COALESCE(NULLIF(?, ''), remarks), updated_at = ? WHERE id = ?",
        (status, remarks, now, application_id),
    )
    add_event(conn, application_id, status, meta["label"], remarks, actor=actor)


APPLICATION_SELECT = """
    SELECT a.*, s.name AS scholarship_name, s.slug AS scholarship_slug, s.provider,
           s.category, s.amount, s.deadline, s.official_link, s.amount_value
    FROM applications a JOIN scholarships s ON s.id = a.scholarship_id
"""


def enrich_application(row: sqlite3.Row | dict) -> dict:
    data = dict(row)
    meta = config.STATUS_META.get(data.get("status"), {})
    data["status_meta"] = meta
    data["progress"] = meta.get("progress", 0)
    data["deadline_label"] = deadline_label(data.get("deadline"))
    data["created_label"] = humanise_date(data.get("created_at"))
    data["updated_label"] = humanise_date(data.get("updated_at"))
    return data


def user_applications(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        APPLICATION_SELECT + " WHERE a.user_id = ? ORDER BY a.updated_at DESC", (user_id,)
    ).fetchall()
    return [enrich_application(r) for r in rows]


def get_application(conn: sqlite3.Connection, application_id: int) -> Optional[dict]:
    row = conn.execute(APPLICATION_SELECT + " WHERE a.id = ?", (application_id,)).fetchone()
    return enrich_application(row) if row else None


def get_application_by_no(conn: sqlite3.Connection, app_no: str) -> Optional[dict]:
    row = conn.execute(
        APPLICATION_SELECT + " WHERE UPPER(a.application_no) = UPPER(?)", (app_no.strip(),)
    ).fetchone()
    return enrich_application(row) if row else None


def application_events(conn: sqlite3.Connection, application_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM application_events WHERE application_id = ? ORDER BY created_at ASC, id ASC",
        (application_id,),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["meta"] = config.STATUS_META.get(d["status"], {})
        d["date_label"] = humanise_date(d["created_at"])
        d["time_label"] = datetime_label(d["created_at"])
        out.append(d)
    return out


def application_stats(conn: sqlite3.Connection, user_id: Optional[int] = None) -> dict:
    where, params = ("WHERE user_id = ?", (user_id,)) if user_id else ("", ())
    total = conn.execute(f"SELECT COUNT(*) n FROM applications {where}", params).fetchone()["n"]
    by_status = {
        r["status"]: r["n"]
        for r in conn.execute(
            f"SELECT status, COUNT(*) n FROM applications {where} GROUP BY status", params
        ).fetchall()
    }
    active = sum(
        by_status.get(s, 0) for s in ["submitted", "under_review", "documents_verified", "on_hold"]
    )
    approved = by_status.get("approved", 0) + by_status.get("disbursed", 0)
    if user_id:
        awarded = conn.execute(
            """SELECT COALESCE(SUM(s.amount_value), 0) v FROM applications a
               JOIN scholarships s ON s.id = a.scholarship_id
               WHERE a.user_id = ? AND a.status IN ('approved','disbursed')""",
            (user_id,),
        ).fetchone()["v"]
    else:
        awarded = 0
    return {
        "total": total,
        "active": active,
        "approved": approved,
        "rejected": by_status.get("rejected", 0),
        "disbursed": by_status.get("disbursed", 0),
        "by_status": by_status,
        "awarded": awarded,
    }


def saved_ids(conn: sqlite3.Connection, user_id: Optional[int]) -> set[int]:
    if not user_id:
        return set()
    return {
        r["scholarship_id"]
        for r in conn.execute(
            "SELECT scholarship_id FROM saved_scholarships WHERE user_id = ?", (user_id,)
        ).fetchall()
    }


def saved_scholarships(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        """SELECT s.* FROM saved_scholarships sv
           JOIN scholarships s ON s.id = sv.scholarship_id
           WHERE sv.user_id = ? ORDER BY sv.created_at DESC""",
        (user_id,),
    ).fetchall()
    out = []
    for row in rows:
        d = dict(row)
        decorate_scholarship(d)
        out.append(d)
    return out


def applied_scholarship_ids(conn: sqlite3.Connection, user_id: Optional[int]) -> set[int]:
    if not user_id:
        return set()
    return {
        r["scholarship_id"]
        for r in conn.execute(
            "SELECT scholarship_id FROM applications WHERE user_id = ?", (user_id,)
        ).fetchall()
    }
