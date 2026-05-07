# AgriGrow — Flask Python Backend

This is the Python/Flask replacement for the original Node.js/Express backend.
Every API endpoint is identical — the frontend (`AgriGrow.html`) requires **no changes**.

---

## Folder Structure

```
flask-backend/
├── app.py                  ← Entry point (replaces server.js)
├── requirements.txt        ← Python packages to install
├── .env                    ← Database & JWT secrets
│
├── db/
│   └── database.py         ← MySQL connection + db_run/db_get/db_all helpers
│
├── middleware/
│   └── auth_middleware.py  ← JWT @require_auth and @admin_only decorators
│
└── routes/
    ├── auth.py             ← POST /api/auth/register  & /api/auth/login
    ├── profile.py          ← GET/PUT /api/profile
    ├── progress.py         ← GET /api/progress, POST /api/progress/lesson & /task
    ├── tracker.py          ← GET/POST /api/tracker
    ├── community.py        ← GET/POST/DELETE /api/posts, POST /api/posts/:id/like
    ├── leaderboard.py      ← GET /api/leaderboard
    └── admin.py            ← GET/POST/DELETE /api/admin/stats, /users, /modules
```

---

## Setup

### 1. Make sure MySQL is running and the database exists

```sql
-- Run this once in MySQL Workbench or terminal:
CREATE DATABASE IF NOT EXISTS agrigrow;
```

Then run the schema:
```
mysql -u root -p agrigrow < ../agrigrow-backend/schema.sql
```

### 2. Check the `.env` file

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=agrigrow
JWT_SECRET=agrigrow_super_secret_jwt_key_2026
PORT=5000
```

### 3. Install Python packages

```bash
pip install -r requirements.txt
```

### 4. Start the server

```bash
python app.py
```

The server starts at **http://localhost:5000**

- App:    http://localhost:5000/AgriGrow.html
- Health: http://localhost:5000/api/health

---

## JS → Python Quick Reference

| Node.js / Express          | Flask / Python equivalent             |
|----------------------------|---------------------------------------|
| `require('express')`       | `from flask import Flask, Blueprint`  |
| `app.use('/api/x', router)`| `app.register_blueprint(bp, url_prefix='/api/x')` |
| `router.get('/', fn)`      | `@bp.route('/', methods=['GET'])`     |
| `req.body`                 | `request.get_json()`                  |
| `req.params.id`            | `<int:id>` in route + function arg    |
| `req.headers.authorization`| `request.headers.get('Authorization')`|
| `res.json({...})`          | `return jsonify({...})`               |
| `res.status(400).json(...)` | `return jsonify(...), 400`           |
| `next()` middleware        | `@require_auth` decorator             |
| `process.env.VAR`          | `os.getenv('VAR')`                    |
| `bcrypt.hash(pw, 10)`      | `bcrypt.hashpw(pw.encode(), bcrypt.gensalt())` |
| `jwt.sign({...}, secret)`  | `jwt.encode({...}, secret, algorithm='HS256')` |
