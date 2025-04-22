import sqlite3
from datetime import datetime, timedelta
import threading

# Thread-local storage for connections
_local = threading.local()

def get_db():
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect("goldsight.db", timeout=60)
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn.execute("PRAGMA cache_size=-4000")
    return _local.conn

def init_db():
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (user_id INTEGER PRIMARY KEY,
                      subscription_end TEXT,
                      referral_code TEXT UNIQUE,
                      referred_by TEXT,
                      vip_status INTEGER DEFAULT 0,
                      join_date TEXT DEFAULT CURRENT_TIMESTAMP)''')

        # Add indexes for better query performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_referral ON users(referral_code)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_subscription ON users(subscription_end)')

        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

def add_user(user_id, referral=None):
    conn = get_db()
    c = conn.cursor()
    ref_code = f"GS{user_id}"
    try:
        c.execute("INSERT OR IGNORE INTO users (user_id, referral_code, referred_by) VALUES (?, ?, ?)", 
                 (user_id, ref_code, referral))
        conn.commit()
        return ref_code
    except Exception as e:
        print(f"Error adding user: {e}")
        return None

def approve_vip(user_id, plan):
    try:
        days = 7 if plan == "weekly" else 30
        sub_end = (datetime.now() + timedelta(days=days)).isoformat()
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET subscription_end=?, vip_status=1 WHERE user_id=?", 
                 (sub_end, user_id))
        c.execute("SELECT referred_by FROM users WHERE user_id=?", (user_id,))
        referrer = c.fetchone()
        commission = 3 if plan == "biweekly" else 5
        conn.commit()
        return referrer[0] if referrer and referrer[0] else None, commission
    except Exception as e:
        print(f"Error approving VIP: {e}")
        return None, 0

def get_user(user_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return c.fetchone()
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def check_subscriptions():
    conn = sqlite3.connect("goldsight.db")
    c = conn.cursor()
    now = datetime.now()
    c.execute("SELECT user_id, subscription_end FROM users WHERE vip_status=1")
    expired = []
    reminders = []
    for user_id, sub_end in c.fetchall():
        sub_end_dt = datetime.fromisoformat(sub_end)
        if sub_end_dt < now:
            c.execute("UPDATE users SET vip_status=0 WHERE user_id=?", (user_id,))
            expired.append(user_id)
        elif (sub_end_dt - now).days <= 2:
            reminders.append(user_id)
    conn.commit()
    conn.close()
    return expired, reminders