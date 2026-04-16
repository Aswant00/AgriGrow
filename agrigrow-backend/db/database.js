// db/database.js — SQLite database setup using sqlite3
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const DB_PATH = path.join(__dirname, 'agrigrow.db');

// Create a database instance
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) {
    console.error('Failed to open database:', err.message);
    process.exit(1);
  }
  console.log('📦 SQLite database connected:', DB_PATH);
});

// Enable foreign keys and WAL mode
db.run('PRAGMA foreign_keys = ON');
db.run('PRAGMA journal_mode = WAL');

// ── Promise wrappers for cleaner async/await usage ────────────────────────────
function dbRun(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) reject(err);
      else resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
}

function dbGet(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

function dbAll(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

// ── Initialize tables ─────────────────────────────────────────────────────────
async function initDb() {
  await dbRun(`CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'farmer',
    region      TEXT    DEFAULT '',
    crop_type   TEXT    DEFAULT '',
    farm_size   TEXT    DEFAULT '',
    experience  TEXT    DEFAULT '',
    points      INTEGER DEFAULT 0,
    streak      INTEGER DEFAULT 3,
    created_at  TEXT    DEFAULT (datetime('now'))
  )`);

  await dbRun(`CREATE TABLE IF NOT EXISTS completed_lessons (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    lesson_id    TEXT    NOT NULL,
    pts          INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, lesson_id)
  )`);

  await dbRun(`CREATE TABLE IF NOT EXISTS today_tasks (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER NOT NULL,
    task_id  TEXT    NOT NULL,
    done     INTEGER DEFAULT 0,
    date     TEXT    DEFAULT (date('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, task_id, date)
  )`);

  await dbRun(`CREATE TABLE IF NOT EXISTS badges (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER NOT NULL,
    badge_id TEXT    NOT NULL,
    earned   INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, badge_id)
  )`);

  await dbRun(`CREATE TABLE IF NOT EXISTS activity_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    practices  TEXT    NOT NULL,
    notes      TEXT    DEFAULT '',
    date       TEXT    NOT NULL,
    pts        INTEGER NOT NULL DEFAULT 0,
    has_proof  INTEGER DEFAULT 0,
    created_at TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
  )`);

  await dbRun(`CREATE TABLE IF NOT EXISTS posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    author          TEXT    NOT NULL,
    is_expert       INTEGER DEFAULT 0,
    tag             TEXT    DEFAULT 'General',
    body            TEXT    NOT NULL,
    likes           INTEGER DEFAULT 0,
    reply_author    TEXT    DEFAULT NULL,
    reply_text      TEXT    DEFAULT NULL,
    reply_is_expert INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
  )`);

  await dbRun(`CREATE TABLE IF NOT EXISTS post_likes (
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, post_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
  )`);

  await dbRun(`CREATE TABLE IF NOT EXISTS custom_modules (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT    NOT NULL,
    category         TEXT    NOT NULL,
    difficulty       TEXT    NOT NULL DEFAULT 'Beginner',
    icon             TEXT    DEFAULT 'eco',
    icon_color       TEXT    DEFAULT '#2e7d32',
    description      TEXT    NOT NULL,
    duration         TEXT    DEFAULT '30 min',
    expert_verified  INTEGER DEFAULT 0,
    created_by       INTEGER,
    created_at       TEXT    DEFAULT (datetime('now'))
  )`);

  console.log('✅ Database tables ready');
}

// ── Helpers for new users ─────────────────────────────────────────────────────
const ALL_BADGES = ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'];

async function initBadgesForUser(userId) {
  for (const bid of ALL_BADGES) {
    await dbRun('INSERT OR IGNORE INTO badges (user_id, badge_id, earned) VALUES (?, ?, 0)', [userId, bid]);
  }
}

async function initTasksForUser(userId, date) {
  const tasks = ['t1', 't2', 't3'];
  for (const tid of tasks) {
    await dbRun('INSERT OR IGNORE INTO today_tasks (user_id, task_id, date, done) VALUES (?, ?, ?, 0)', [userId, tid, date]);
  }
}

module.exports = { db, dbRun, dbGet, dbAll, initBadgesForUser, initTasksForUser, initDb };
