# 🎓 Scholarship Hub

A full-stack government scholarship portal built with HTML/CSS/JS + Node.js + Express + MySQL.

---

## 📁 Project Structure

```
ScholarshipHub/
│
├── frontend/
│   ├── index.html                    ← Homepage
│   ├── assets/
│   │   ├── css/
│   │   │   └── main.css              ← All styles
│   │   ├── js/
│   │   │   ├── api.js                ← All API calls to backend
│   │   │   └── script.js             ← Dropdown, carousel, tracker UI
│   │   └── images/                   ← Add your images here
│   └── pages/
│       ├── international.html
│       ├── national.html
│       ├── state.html
│       ├── private.html
│       ├── faq.html
│       ├── contact.html
│       └── admin.html
│
├── backend/
│   ├── server.js                     ← App entry point
│   ├── package.json
│   ├── .env.example                  ← Copy to .env and fill in values
│   ├── config/
│   │   └── db.js                     ← MySQL connection pool
│   ├── controllers/
│   │   ├── authController.js
│   │   ├── scholarshipController.js
│   │   ├── applicationController.js
│   │   ├── announcementController.js
│   │   ├── contactController.js
│   │   └── adminController.js
│   ├── middleware/
│   │   ├── auth.js                   ← JWT middleware
│   │   └── validate.js               ← Input validation
│   ├── routes/
│   │   ├── auth.js
│   │   ├── scholarships.js
│   │   ├── applications.js
│   │   ├── announcements.js
│   │   ├── contact.js
│   │   └── admin.js
│   ├── database/
│   │   └── schema.sql                ← Run once to create all tables + seed data
│   └── utils/
│       ├── mailer.js                 ← Nodemailer email helper
│       └── helpers.js                ← generateOTR, generateAppId, formatDate
│
└── README.md
```

---

## ⚡ Setup Guide

### Step 1 — Install Requirements
- Node.js: https://nodejs.org (LTS version)
- MySQL: https://dev.mysql.com/downloads/

### Step 2 — Create Database
```bash
mysql -u root -p < backend/database/schema.sql
```

### Step 3 — Configure Environment
```bash
cd backend
cp .env.example .env
# Open .env and fill in your values
```

### Step 4 — Install Dependencies & Start Backend
```bash
cd backend
npm install
npm run dev
# API runs at http://localhost:5000
```

### Step 5 — Open Frontend
Open `frontend/index.html` using VS Code Live Server.
Make sure FRONTEND_URL in .env matches your Live Server port.

---

## 🔑 Admin Credentials
- URL:      frontend/pages/admin.html
- Email:    admin@scholarshiphub.com
- Password: Admin@123

---

## 🌐 API Reference

| Method | Endpoint                          | Auth     | Description              |
|--------|-----------------------------------|----------|--------------------------|
| POST   | /api/auth/register                | None     | Register new student     |
| POST   | /api/auth/login                   | None     | Login                    |
| GET    | /api/auth/profile                 | Student  | Get own profile          |
| GET    | /api/scholarships                 | None     | List / filter            |
| GET    | /api/scholarships/:id             | None     | Single scholarship       |
| POST   | /api/applications                 | Student  | Submit application       |
| GET    | /api/applications/my              | Student  | My applications          |
| GET    | /api/applications/track/:app_id   | None     | Public status tracker    |
| GET    | /api/announcements                | None     | All announcements        |
| POST   | /api/contact                      | None     | Send contact message     |
| GET    | /api/admin/dashboard              | Admin    | Stats overview           |
| GET    | /api/admin/scholarships           | Admin    | All scholarships         |
| POST   | /api/admin/scholarships           | Admin    | Create scholarship       |
| PUT    | /api/admin/scholarships/:id       | Admin    | Update scholarship       |
| DELETE | /api/admin/scholarships/:id       | Admin    | Delete scholarship       |
| GET    | /api/admin/applications           | Admin    | All applications         |
| PUT    | /api/admin/applications/:id/status| Admin    | Update app status        |
| GET    | /api/admin/announcements          | Admin    | All announcements        |
| POST   | /api/admin/announcements          | Admin    | Create announcement      |
| PUT    | /api/admin/announcements/:id      | Admin    | Update announcement      |
| DELETE | /api/admin/announcements/:id      | Admin    | Delete announcement      |

| GET    | /api/admin/messages               | Admin    | Contact messages         |

| GET    | /api/admin/messages               | Admin    | Contact messages         |










hello

