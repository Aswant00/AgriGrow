# MySQL connection and query helpers.

import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()

# Database connection helper

def get_connection():
    """Open and return a new MySQL connection."""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'agrigrow'),
        cursorclass=pymysql.cursors.DictCursor,  # rows returned as dicts
        autocommit=True,
    )

# Test connection
try:
    _test = get_connection()
    _test.close()
    print('🗄️  MySQL database connected successfully!')
except Exception as e:
    print(f'❌ MySQL connection failed: {e}')
    print('   → Check your .env file (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)')
    raise SystemExit(1)


# Execute INSERT/UPDATE/DELETE queries
def db_run(sql, params=()):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return {'lastID': cur.lastrowid, 'changes': cur.rowcount}
    finally:
        conn.close()


# Fetch a single row
def db_get(sql, params=()):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    finally:
        conn.close()


# Fetch multiple rows
def db_all(sql, params=()):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


# Seed new user data
ALL_BADGES = ['b1', 'b2', 'b3', 'b4', 'b5', 'b6']

def init_badges_for_user(user_id):
    """Insert all 6 badges for a new user (earned = 0)."""
    for bid in ALL_BADGES:
        db_run(
            'INSERT IGNORE INTO badges (user_id, badge_id, earned) VALUES (%s, %s, 0)',
            (user_id, bid)
        )

def init_tasks_for_user(user_id, date):
    """Insert today's 3 daily tasks for a new user."""
    for tid in ['t1', 't2', 't3']:
        db_run(
            'INSERT IGNORE INTO today_tasks (user_id, task_id, date, done) VALUES (%s, %s, %s, 0)',
            (user_id, tid, date)
        )
