# database.py
import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect("goldsight.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, 
                  subscription_end TEXT, 
                  referral_code TEXT, 
                  referred_by TEXT, 
                  vip_status INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def add_user(user_id, referral=None):
    conn = sqlite3.connect("goldsight.db")
    c = conn.cursor()
    ref_code = f"REF{user_id}"
    c.execute("INSERT OR IGNORE INTO users (user_id, referral_code, referred_by) VALUES (?, ?, ?)", 
              (user_id, ref_code, referral))
    conn.commit()
    conn.close()
    return ref_code

def approve_vip(user_id, plan):
    days = 14 if plan == "biweekly" else 30
    sub_end = (datetime.now() + timedelta(days=days)).isoformat()
    conn = sqlite3.connect("goldsight.db")
    c = conn.cursor()
    c.execute("UPDATE users SET subscription_end=?, vip_status=1 WHERE user_id=?", (sub_end, user_id))
    c.execute("SELECT referred_by FROM users WHERE user_id=?", (user_id,))
    referrer = c.fetchone()
    commission = 3 if plan == "biweekly" else 5
    conn.commit()
    conn.close()
    return referrer[0] if referrer and referrer[0] else None, commission

def get_user(user_id):
    conn = sqlite3.connect("goldsight.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

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
    return expired,reminders
