import shutil
import sqlite3
import unittest
from pathlib import Path

import database


class DatabaseTests(unittest.TestCase):
    def test_save_idea_intake_upserts_structured_row(self) -> None:
        tmp_dir = Path("tests/.tmp/database")
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        original_path = database.DB_PATH
        temp_db = tmp_dir / "leads.db"
        try:
            database.DB_PATH = str(temp_db)
            database.init_db()

            database.save_idea_intake(
                {
                    "session_id": "session-1",
                    "full_name": "Peter",
                    "email": "peter@example.com",
                    "phone": "",
                    "idea_summary": "Fitness app for busy workers",
                    "problem": "Busy workers miss workouts",
                    "target_users": "Busy workers",
                    "primary_goal": "Build and validate the idea",
                    "current_stage": "discovery",
                    "budget": "standard",
                    "timeline": "next month",
                    "refined_summary": "Idea: Fitness app for busy workers",
                    "conversation_summary": "Idea: Fitness app for busy workers",
                    "qa_history": [{"role": "user", "text": "I want a fitness app"}],
                    "latest_question": "What problem does it solve?",
                    "latest_answer": "It helps busy workers stay fit",
                    "status": "in_progress",
                }
            )

            database.save_idea_intake(
                {
                    "session_id": "session-1",
                    "full_name": "Peter Parker",
                    "email": "peter@example.com",
                    "phone": "",
                    "idea_summary": "Fitness app for busy workers",
                    "problem": "Busy workers miss workouts",
                    "target_users": "Busy workers",
                    "primary_goal": "Build and validate the idea",
                    "current_stage": "refinement",
                    "budget": "standard",
                    "timeline": "next month",
                    "refined_summary": "Idea: Fitness app for busy workers | refined",
                    "conversation_summary": "Idea: Fitness app for busy workers | refined",
                    "qa_history": [{"role": "user", "text": "I want a fitness app"}],
                    "latest_question": "What problem does it solve?",
                    "latest_answer": "It helps busy workers stay fit",
                    "status": "active",
                }
            )

            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT full_name, current_stage, refined_summary, status, qa_history FROM idea_intakes WHERE session_id = ?",
                    ("session-1",),
                )
                row = cursor.fetchone()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0], "Peter Parker")
            self.assertEqual(row[1], "refinement")
            self.assertIn("refined", row[2])
            self.assertEqual(row[3], "active")
            self.assertIn("I want a fitness app", row[4])
        finally:
            database.DB_PATH = original_path
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
