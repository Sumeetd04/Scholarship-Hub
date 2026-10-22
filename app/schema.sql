-- Scholarship Hub · SQLite schema
-- Every table is additive; init_db() is safe to run repeatedly.

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    phone         TEXT,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'student',
    otr           TEXT    UNIQUE,
    dob           TEXT,
    gender        TEXT,
    category      TEXT,
    annual_income INTEGER,
    state         TEXT,
    institute     TEXT,
    course        TEXT,
    level         TEXT,
    created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scholarships (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    slug          TEXT    NOT NULL UNIQUE,
    name          TEXT    NOT NULL,
    provider      TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    level         TEXT    NOT NULL,
    state         TEXT    NOT NULL DEFAULT 'All India',
    amount        TEXT    NOT NULL,
    amount_value  INTEGER NOT NULL DEFAULT 0,
    deadline      TEXT    NOT NULL,
    description   TEXT    NOT NULL,
    eligibility   TEXT    NOT NULL,
    benefits      TEXT    NOT NULL,
    documents     TEXT    NOT NULL,
    apply_mode    TEXT    NOT NULL,
    official_link TEXT    NOT NULL,
    tags          TEXT    NOT NULL DEFAULT '',
    income_limit  INTEGER NOT NULL DEFAULT 0,
    gender        TEXT    NOT NULL DEFAULT 'Any',
    minority      INTEGER NOT NULL DEFAULT 0,
    disability    INTEGER NOT NULL DEFAULT 0,
    awards        TEXT    NOT NULL DEFAULT '',
    featured      INTEGER NOT NULL DEFAULT 0,
    status        TEXT    NOT NULL DEFAULT 'open',
    created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sch_category ON scholarships(category);
CREATE INDEX IF NOT EXISTS idx_sch_state    ON scholarships(state);
CREATE INDEX IF NOT EXISTS idx_sch_level    ON scholarships(level);
CREATE INDEX IF NOT EXISTS idx_sch_deadline ON scholarships(deadline);

CREATE TABLE IF NOT EXISTS applications (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    application_no TEXT    NOT NULL UNIQUE,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scholarship_id INTEGER NOT NULL REFERENCES scholarships(id) ON DELETE CASCADE,
    status         TEXT    NOT NULL DEFAULT 'submitted',
    full_name      TEXT    NOT NULL,
    dob            TEXT,
    gender         TEXT,
    category       TEXT,
    annual_income  INTEGER,
    state          TEXT,
    institute      TEXT,
    course         TEXT,
    level          TEXT,
    note           TEXT,
    remarks        TEXT,
    created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, scholarship_id)
);

CREATE INDEX IF NOT EXISTS idx_app_user   ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_app_no     ON applications(application_no);

CREATE TABLE IF NOT EXISTS application_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    status         TEXT    NOT NULL,
    title          TEXT    NOT NULL,
    note           TEXT,
    actor          TEXT    NOT NULL DEFAULT 'system',
    created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_event_app ON application_events(application_id);

CREATE TABLE IF NOT EXISTS saved_scholarships (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scholarship_id INTEGER NOT NULL REFERENCES scholarships(id) ON DELETE CASCADE,
    created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, scholarship_id)
);

CREATE TABLE IF NOT EXISTS announcements (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    body       TEXT    NOT NULL,
    tag        TEXT    NOT NULL DEFAULT 'General',
    pinned     INTEGER NOT NULL DEFAULT 0,
    link       TEXT,
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    subject    TEXT,
    message    TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
