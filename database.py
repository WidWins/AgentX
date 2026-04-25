import os
import re
import sqlite3
import json

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


def _get_existing_idea_columns(cursor):
    cursor.execute("PRAGMA table_info(idea_intakes)")
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

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS idea_intakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                idea_summary TEXT,
                problem TEXT,
                target_users TEXT,
                primary_goal TEXT,
                current_stage TEXT,
                budget TEXT,
                timeline TEXT,
                refined_summary TEXT,
                conversation_summary TEXT,
                qa_history TEXT,
                latest_question TEXT,
                latest_answer TEXT,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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

        existing_idea_columns = _get_existing_idea_columns(cursor)
        idea_columns = {
            "session_id": "TEXT",
            "full_name": "TEXT",
            "email": "TEXT",
            "phone": "TEXT",
            "idea_summary": "TEXT",
            "problem": "TEXT",
            "target_users": "TEXT",
            "primary_goal": "TEXT",
            "current_stage": "TEXT",
            "budget": "TEXT",
            "timeline": "TEXT",
            "refined_summary": "TEXT",
            "conversation_summary": "TEXT",
            "qa_history": "TEXT",
            "latest_question": "TEXT",
            "latest_answer": "TEXT",
            "status": "TEXT",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        }
        for column_name, column_type in idea_columns.items():
            if column_name not in existing_idea_columns:
                cursor.execute(f"ALTER TABLE idea_intakes ADD COLUMN {column_name} {column_type}")

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


def save_idea_intake(payload):
    """Insert or update a structured idea intake record in the dedicated table."""
    record = dict(payload or {})
    qa_history = record.get("qa_history", [])
    if not isinstance(qa_history, str):
        record["qa_history"] = json.dumps(qa_history, ensure_ascii=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO idea_intakes (
                session_id,
                full_name,
                email,
                phone,
                idea_summary,
                problem,
                target_users,
                primary_goal,
                current_stage,
                budget,
                timeline,
                refined_summary,
                conversation_summary,
                qa_history,
                latest_question,
                latest_answer,
                status,
                created_at,
                updated_at
            ) VALUES (
                :session_id,
                :full_name,
                :email,
                :phone,
                :idea_summary,
                :problem,
                :target_users,
                :primary_goal,
                :current_stage,
                :budget,
                :timeline,
                :refined_summary,
                :conversation_summary,
                :qa_history,
                :latest_question,
                :latest_answer,
                :status,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT(session_id) DO UPDATE SET
                full_name = excluded.full_name,
                email = excluded.email,
                phone = excluded.phone,
                idea_summary = excluded.idea_summary,
                problem = excluded.problem,
                target_users = excluded.target_users,
                primary_goal = excluded.primary_goal,
                current_stage = excluded.current_stage,
                budget = excluded.budget,
                timeline = excluded.timeline,
                refined_summary = excluded.refined_summary,
                conversation_summary = excluded.conversation_summary,
                qa_history = excluded.qa_history,
                latest_question = excluded.latest_question,
                latest_answer = excluded.latest_answer,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            record,
        )
        conn.commit()


def load_idea_intakes():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, full_name, email, phone, idea_summary, problem, target_users, primary_goal, current_stage, budget, timeline, refined_summary, conversation_summary, qa_history, latest_question, latest_answer, status, created_at, updated_at FROM idea_intakes ORDER BY updated_at DESC")
        rows = cursor.fetchall()
    columns = [
        "session_id",
        "full_name",
        "email",
        "phone",
        "idea_summary",
        "problem",
        "target_users",
        "primary_goal",
        "current_stage",
        "budget",
        "timeline",
        "refined_summary",
        "conversation_summary",
        "qa_history",
        "latest_question",
        "latest_answer",
        "status",
        "created_at",
        "updated_at",
    ]
    return [dict(zip(columns, row)) for row in rows]


init_db()
