import sqlite3
import threading
from datetime import datetime, timedelta

DB_FILE = "goldsight.db"
DB_LOCK = threading.Lock()  # Prevents race conditions in multithreading

def get_db_connection():
    """Creates and returns a thread-safe database connection."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database with necessary tables."""
    with DB_LOCK, get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, 
                subscription_end TEXT, 
                referral_code TEXT, 
                referred_by INTEGER, 
                vip_status INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

def add_user(user_id, referral=None):
    """Adds a user if they don't already exist."""
    ref_code = f"REF{user_id}"
    with DB_LOCK, get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO users (user_id, referral_code, referred_by) 
            VALUES (?, ?, ?)
        """, (user_id, ref_code, referral))
        conn.commit()
    return ref_code

def approve_vip(user_id, plan):
    """Approves VIP membership and calculates commissions."""
    days = 14 if plan == "biweekly" else 30
    sub_end = (datetime.now() + timedelta(days=days)).isoformat()

    with DB_LOCK, get_db_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET subscription_end=?, vip_status=1 WHERE user_id=?", 
                  (sub_end, user_id))
        c.execute("SELECT referred_by FROM users WHERE user_id=?", (user_id,))
        referrer = c.fetchone()
        commission = 3 if plan == "biweekly" else 5  # 10% of $30 or $50
        conn.commit()

    return referrer["referred_by"] if referrer and referrer["referred_by"] else None, commission

def get_user(user_id):
    """Fetches user details."""
    with DB_LOCK, get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return c.fetchone()

def check_subscriptions():
    """Checks for expired subscriptions and upcoming renewals."""
    expired, reminders = [], []
    now = datetime.now()

    with DB_LOCK, get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, subscription_end FROM users WHERE vip_status=1")
        for row in c.fetchall():
            user_id, sub_end = row["user_id"], row["subscription_end"]
            sub_end_dt = datetime.fromisoformat(sub_end) if sub_end else None

            if sub_end_dt and sub_end_dt < now:
                c.execute("UPDATE users SET vip_status=0 WHERE user_id=?", (user_id,))
                expired.append(user_id)
            elif sub_end_dt and (sub_end_dt - now).days <= 2:
                reminders.append(user_id)
        conn.commit()

    return expired, reminders