"""Application configuration, read from environment variables with sane defaults."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader so the app works without python-dotenv."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")

DATA_DIR = Path(os.getenv("SCHOLARSHIP_DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.getenv("SCHOLARSHIP_DB", DATA_DIR / "scholarship_hub.db"))

SECRET_KEY = os.getenv("SECRET_KEY", "scholarship-hub-dev-secret-change-in-production-2026")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "168"))
COOKIE_NAME = "sh_session"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@scholarshiphub.in")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")
DEMO_STUDENT_EMAIL = "aarav.sharma@example.com"
DEMO_STUDENT_PASSWORD = "Student@123"

APP_NAME = "Scholarship Hub"
APP_TAGLINE = "Every scholarship in India. One glass pane."
SUPPORT_EMAIL = "help@scholarshiphub.in"

# Application lifecycle -------------------------------------------------------
STATUS_FLOW = ["submitted", "under_review", "documents_verified", "approved", "disbursed"]

STATUS_META = {
    "submitted": {
        "label": "Submitted",
        "short": "Received by portal",
        "progress": 15,
        "tone": "info",
        "icon": "send",
        "note": "Your application has been received. Keep your application number safe.",
    },
    "under_review": {
        "label": "Under Review",
        "short": "Being verified",
        "progress": 35,
        "tone": "warning",
        "icon": "search",
        "note": "The nodal officer is verifying your details and documents.",
    },
    "documents_verified": {
        "label": "Documents Verified",
        "short": "Verification cleared",
        "progress": 55,
        "tone": "accent",
        "icon": "check",
        "note": "Documents verified. Your application is now with the sanction committee.",
    },
    "approved": {
        "label": "Approved",
        "short": "Sanctioned",
        "progress": 80,
        "tone": "success",
        "icon": "badge",
        "note": "Congratulations! Your scholarship has been sanctioned.",
    },
    "disbursed": {
        "label": "Amount Disbursed",
        "short": "Money credited",
        "progress": 100,
        "tone": "success",
        "icon": "wallet",
        "note": "The scholarship amount has been transferred to your registered bank account.",
    },
    "on_hold": {
        "label": "Action Required",
        "short": "Needs your attention",
        "progress": 45,
        "tone": "warning",
        "icon": "alert",
        "note": "Additional information is required. Please check the remarks and update your details.",
    },
    "rejected": {
        "label": "Not Approved",
        "short": "Rejected",
        "progress": 100,
        "tone": "danger",
        "icon": "x",
        "note": "Unfortunately this application was not approved. See remarks for details.",
    },
    "withdrawn": {
        "label": "Withdrawn",
        "short": "Withdrawn by student",
        "progress": 100,
        "tone": "muted",
        "icon": "minus",
        "note": "You withdrew this application.",
    },
}

CATEGORY_VALUES = [
    "Central Government",
    "State Government",
    "Private & Corporate",
    "Trust & Foundation",
]

CATEGORIES = [
    {"name": "Central Government", "blurb": "Ministries & national portals", "icon": "landmark", "accent": "indigo"},
    {"name": "State Government", "blurb": "MahaDBT, ePASS, OASIS & more", "icon": "map", "accent": "cyan"},
    {"name": "Private & Corporate", "blurb": "CSR and company scholarships", "icon": "briefcase", "accent": "amber"},
    {"name": "Trust & Foundation", "blurb": "NGOs and family foundations", "icon": "heart", "accent": "rose"},
]

LEVELS = [
    "Class 9-10",
    "Class 11-12",
    "Diploma / ITI",
    "Undergraduate",
    "Postgraduate",
    "Doctoral",
    "Multiple Levels",
]

STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu & Kashmir", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "All India",
]

SOCIAL_CATEGORIES = ["General", "OBC", "SC", "ST", "EWS", "Minority", "DNT"]
GENDERS = ["Female", "Male", "Other"]
