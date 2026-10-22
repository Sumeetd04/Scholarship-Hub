# 🎓 Scholarship Hub

**Every scholarship in India. One glass pane.**

A complete, student-first scholarship portal built with **Python · FastAPI · Jinja2 · SQLite**.
Browse 90+ verified central, state, private and foundation scholarships open to Indian students —
then **track every application from submission to disbursal** with one submission ID.

> The application tracker is the heart of the product: every submission gets a permanent ID
> (`SH-YYYY-XXXXXX`), a timestamped timeline and a plain-language "what happens next".

---

## ✨ What's inside

| Area | Highlights |
| --- | --- |
| **Catalogue** | 93 curated Indian schemes (NSP, MahaDBT, ePASS, OASIS, e-Grantz, MYSY, CSR & foundations) with deadlines, income ceilings, eligibility, benefits and documents |
| **Tracking** | Public tracker (submission ID + DOB), owner dashboard, full event timeline, 9 statuses, progress %, officer remarks, DBT disbursal state |
| **Discovery** | Keyword search with live suggestions, filters (category / state / level / gender / closed), sorting, pagination, state directories |
| **Matching** | 6-question eligibility finder + profile-aware recommendations with a transparent 0–100 match score |
| **Student account** | Register / login (JWT in an HttpOnly cookie), OTR generation, saved schemes, applications, profile, password change |
| **Admin console** | KPIs, application pipeline, inline status updates with remarks, scholarship CRUD, notices, support inbox, student directory |
| **Design** | Glassmorphism UI, animated aurora background, dark + light themes, responsive down to 360 px, reduced-motion support, print-friendly receipts |
| **API** | JSON endpoints for search, stats, tracker and the signed-in user; interactive docs at `/api/docs` |

---

## 🚀 Run locally

```bash
# 1. install dependencies
python3 -m pip install -r requirements.txt

# 2. start the app (creates + seeds data/scholarship_hub.db automatically)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** 🎉

No database server, no migrations, no Node build step. The SQLite file is created on first boot
and seeded with the full catalogue, demo students and demo applications.

### Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Student | `aarav.sharma@example.com` | `Student@123` |
| Student (girls' schemes) | `priya.patil@example.com` | `Student@123` |
| Admin | `admin@scholarshiphub.in` | `Admin@123` |

A pre-filled demo tracker is linked on the homepage:
`SH-2026-101043` with DOB `2005-04-18`.

---

## 🧱 Project structure

```
Scholarship-Hub/
├── app/
│   ├── main.py               FastAPI app, middleware, exception handlers
│   ├── config.py             Settings, statuses, categories, states
│   ├── database.py           SQLite connection + schema bootstrap
│   ├── schema.sql            7 tables
│   ├── security.py           bcrypt, JWT, current-user dependencies
│   ├── services.py           Catalogue queries, matching, applications
│   ├── seed.py               Curated Indian scholarship catalogue + demo data
│   ├── templating.py         Jinja filters/globals + flash redirects
│   ├── routers/
│   │   ├── public.py         Home, about, FAQ, contact, notices
│   │   ├── auth.py           Register / login / logout
│   │   ├── scholarships.py   Catalogue, detail, states, finder
│   │   ├── applications.py   Dashboard, apply, saved, profile
│   │   ├── tracker.py        The application tracker
│   │   ├── admin.py          Admin console
│   │   └── api.py            JSON API
│   ├── templates/            Jinja2 (base, 20 pages, admin, partials)
│   └── static/
│       ├── css/main.css      Glass design system (dark + light)
│       └── js/app.js         Theme, menu, search suggestions, toasts
├── data/                     SQLite database (gitignored)
├── requirements.txt
└── .env.example
```

---

## 🔁 The tracking flow

```
submitted → under_review → documents_verified → approved → disbursed
                     ↘ on_hold ↗            ↘ rejected / withdrawn
```

1. **Apply** — the form is prefilled from the student profile; submitting generates the ID and
   writes the first timeline event.
2. **Track publicly** — `/track` accepts the ID + date of birth. Signed-in owners and admins skip
   the DOB check. `?dob=` links keep working after a reload.
3. **Admin moves the file** — `/admin/applications` lets an officer set the next status and add
   remarks; a new event is appended and the student's progress bar updates.
4. **Student sees it** — dashboard rows, the tracker hero, the journey timeline and the JSON API
   all read from the same event log.

Statuses, progress weights, tones and explanatory copy live in `app/config.py` (`STATUS_META`),
so the vocabulary is consistent everywhere.

---

## 🌐 API reference

| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/scholarships?q=&category=&state=&level=&limit=` | — | Search the catalogue |
| `GET` | `/api/scholarships/{slug}` | — | Full scheme payload |
| `GET` | `/api/stats` | — | Catalogue counters |
| `GET` | `/api/track/{app_no}?dob=YYYY-MM-DD` | DOB / owner | Status + timeline |
| `GET` | `/api/me` | Cookie / Bearer | Profile, stats, applications |

Interactive docs: **`/api/docs`**.

```bash
curl "http://localhost:8000/api/scholarships?q=girls&limit=3"
curl "http://localhost:8000/api/track/SH-2026-101043?dob=2005-04-18"
```

---

## 🗃️ Data model

| Table | Purpose |
| --- | --- |
| `users` | Students + admins, OTR, profile fields, bcrypt hash |
| `scholarships` | Catalogue with eligibility/benefits/documents (newline bullet lists) |
| `applications` | One row per student per scheme, unique `application_no` |
| `application_events` | Immutable-ish timeline of status changes |
| `saved_scholarships` | Watchlist |
| `announcements` | Deadline notices |
| `contact_messages` | Support inbox |

Tables are created with `CREATE TABLE IF NOT EXISTS`, so restarts are safe. Delete
`data/scholarship_hub.db` to re-seed from scratch.

---

## ⚙️ Configuration

Copy `.env.example` → `.env` (values are read through `app/config.py`):

| Variable | Default | Notes |
| --- | --- | --- |
| `SECRET_KEY` | dev string | **Change in production** — signs JWTs |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | demo values | Seeded once |
| `SCHOLARSHIP_DB` | `data/scholarship_hub.db` | Absolute path supported |
| `TOKEN_TTL_HOURS` | `168` | Session lifetime |
| `COOKIE_SECURE` | `0` | Set `1` behind HTTPS |

---

## 🎨 Design notes

- **Glass system** — layered `backdrop-filter: blur() saturate()`, 1 px light borders, inset
  highlights and deep ambient shadows. Two themes share one token set.
- **Ambient scene** — three drifting blurred orbs plus a masked grid; disabled automatically
  under `prefers-reduced-motion`.
- **Status language** — colour, icon, progress weight and a one-line explanation per status, used
  in the tracker, dashboard, admin tables and notices.
- **No JS dependency** — every form, filter and status update works without JavaScript; JS adds
  theme persistence, live search, toasts and reveal animations.

---

## ⚠️ Disclaimer

Scholarship Hub is an independent student tool, not a government portal. Scheme details are
compiled for guidance — always verify eligibility, deadlines and fees on the official portal
before applying. No part of this portal charges students a fee.
