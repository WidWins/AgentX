import os
import re
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "leads.db")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s()]{8,}\d)")


def _extract_contact_details(message):
    text = str(message or "")
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)
    email = email_match.group(0).strip() if email_match else None
    phone = phone_match.group(0).strip() if phone_match else None
    return email, phone


def _get_existing_columns(cursor):
    cursor.execute("PRAGMA table_info(leads)")
    return {row[1] for row in cursor.fetchall()}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                stage TEXT,
                email TEXT,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        existing_columns = _get_existing_columns(cursor)
        if "stage" not in existing_columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN stage TEXT")
        if "email" not in existing_columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN email TEXT")
        if "phone" not in existing_columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN phone TEXT")
        if "created_at" not in existing_columns:
            cursor.execute("ALTER TABLE leads ADD COLUMN created_at TEXT")

        conn.commit()


def save_lead(message, stage="general"):
    email, phone = _extract_contact_details(message)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leads (message, stage, email, phone, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (message, stage, email, phone),
        )
        conn.commit()


init_db()
