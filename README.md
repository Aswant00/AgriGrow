#  AgriGrow — Smart Farming Learning Platform

**AgriGrow** is a full-stack web application that empowers farmers with structured agricultural education, practice tracking, community engagement, and a competitive leaderboard — all in one place.

---

## 📸 Features

| Feature | Description |
|---|---|
| Authentication | Secure JWT-based registration & login |
| Learning Modules | Curated farming lessons with progress tracking |
| Practice Tracker | Log daily farming practices and earn points |
| Leaderboard | Compete with other farmers in your region |
| Community | Post questions, share tips, and like others' posts |
| Admin Panel | Manage users, modules, and view platform statistics |

---

## 🗂️ Project Structure

```
AgriGrow/
├── AgriGrow.html          ← Single-page frontend (HTML + Vanilla JS)
│
└── flask-backend/         ← Python / Flask REST API
    ├── app.py             ← App entry point & blueprint registration
    ├── requirements.txt   ← Python dependencies
    ├── .env               ← Environment secrets (not committed)
    │
    ├── db/
    │   └── database.py    ← MySQL connection & db_run/db_get/db_all helpers
    │
    ├── middleware/
    │   └── auth_middleware.py  ← @require_auth & @admin_only JWT decorators
    │
    └── routes/
        ├── auth.py        ← POST /api/auth/register & /login
        ├── profile.py     ← GET/PUT /api/profile
        ├── progress.py    ← GET /api/progress, POST lesson & task
        ├── tracker.py     ← GET/POST /api/tracker
        ├── community.py   ← CRUD /api/posts + likes
        ├── leaderboard.py ← GET /api/leaderboard
        ├── modules.py     ← GET/POST/PUT/DELETE /api/modules (admin)
        └── admin.py       ← GET /api/admin/stats, /users, /modules
```

---

## ⚙️ Tech Stack

- **Frontend**: Vanilla HTML, CSS, JavaScript (single `AgriGrow.html` file)
- **Backend**: Python 3.x · Flask · Flask-CORS
- **Auth**: JWT (PyJWT) · bcrypt password hashing
- **Database**: MySQL (via PyMySQL)
- **Config**: python-dotenv

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Git

---

### 1. Clone the repository

```bash
git clone https://github.com/Aswant00/AgriGrow.git
cd AgriGrow
```

---

### 2. Set up the database

Start MySQL and create the database:

```sql
CREATE DATABASE IF NOT EXISTS agrigrow;
```

---

### 3. Configure environment variables

Create `flask-backend/.env` from the template below:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=agrigrow
JWT_SECRET=agrigrow_super_secret_jwt_key_2026
PORT=5000
```

> ⚠️ **Never commit your `.env` file.** It is listed in `.gitignore`.

---

### 4. Install Python dependencies

```bash
cd flask-backend
pip install -r requirements.txt
```

---

### 5. Start the Flask server

```bash
python app.py
```

The server starts at **http://localhost:5000**

| URL | Description |
|---|---|
| http://localhost:5000/AgriGrow.html | Main application |
| http://localhost:5000/api/health | Health check endpoint |

---

## 🔌 API Overview

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | ❌ | Register new user |
| POST | `/api/auth/login` | ❌ | Login & get JWT |
| GET | `/api/profile` | ✅ | Get current user profile |
| PUT | `/api/profile` | ✅ | Update profile |
| GET | `/api/progress` | ✅ | Get learning progress |
| POST | `/api/progress/lesson` | ✅ | Mark lesson complete |
| GET | `/api/tracker` | ✅ | Get practice logs |
| POST | `/api/tracker` | ✅ | Log a new practice |
| GET | `/api/posts` | ✅ | List community posts |
| POST | `/api/posts` | ✅ | Create a post |
| POST | `/api/posts/:id/like` | ✅ | Like/unlike a post |
| GET | `/api/leaderboard` | ✅ | Get ranked leaderboard |
| GET | `/api/admin/stats` | 🛡️ | Platform statistics |
| GET | `/api/admin/users` | 🛡️ | List all users |
| GET | `/api/modules` | ✅ | List learning modules |
| POST | `/api/modules` | 🛡️ | Create a module |
| PUT | `/api/modules/:id` | 🛡️ | Update a module |
| DELETE | `/api/modules/:id` | 🛡️ | Delete a module |

> **Legend:** ❌ Public · ✅ Requires JWT · 🛡️ Admin only

---

## 🧪 Testing

The platform includes a comprehensive test suite covering:

- Authentication & Profile Management
- Learning Module Progression
- Practice Tracker Logging
- Community & Leaderboard
- Admin Panel Operations

---

## 📄 License

This project is for educational and demonstration purposes.

---

> Built with ❤️ for modern farmers — *AgriGrow, grow smarter.*
