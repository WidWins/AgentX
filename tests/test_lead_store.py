import csv
import json
import shutil
import unittest
from pathlib import Path

from lead_store import export_leads_to_csv, load_leads, save_lead


class LeadStoreTests(unittest.TestCase):
    def test_save_lead_appends_jsonl_record(self) -> None:
        tmp_dir = Path("tests/.tmp/lead_store")
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        destination = tmp_dir / "leads.jsonl"
        try:
            saved_path = save_lead(
                {
                    "full_name": "Aakash Sharma",
                    "lead_type": "qualified",
                    "recommended_package": "Standard",
                    "idea_summary": "Business planning support for a health app",
                    "conversation_summary": "Idea: Health app | Problem: unclear business structure",
                },
                destination=destination,
            )

            self.assertEqual(saved_path, destination)
            lines = destination.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)

            record = json.loads(lines[0])
            self.assertEqual(record["full_name"], "Aakash Sharma")
            self.assertEqual(record["lead_type"], "qualified")
            self.assertEqual(record["conversation_summary"], "Idea: Health app | Problem: unclear business structure")
            self.assertIn("captured_at", record)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_load_leads_returns_saved_records(self) -> None:
        tmp_dir = Path("tests/.tmp/lead_store")
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        destination = tmp_dir / "leads.jsonl"
        try:
            save_lead({"full_name": "Lead One", "idea_summary": "Idea one"}, destination=destination)
            save_lead({"full_name": "Lead Two", "idea_summary": "Idea two"}, destination=destination)

            records = load_leads(destination)

            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["full_name"], "Lead One")
            self.assertEqual(records[1]["full_name"], "Lead Two")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_export_leads_to_csv_writes_expected_columns(self) -> None:
        tmp_dir = Path("tests/.tmp/lead_store")
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        source = tmp_dir / "leads.jsonl"
        destination = tmp_dir / "leads.csv"
        try:
            save_lead(
                {
                    "full_name": "Aakash Sharma",
                    "email": "aakash@example.com",
                    "phone": "+91-9999999999",
                    "lead_type": "qualified",
                    "recommended_package": "Standard",
                    "idea_summary": "Business planning support for a health app",
                    "conversation_summary": "Idea: Health app | Problem: unclear business structure",
                },
                destination=source,
            )

            exported = export_leads_to_csv(source=source, destination=destination)

            self.assertEqual(exported, destination)
            with destination.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["full_name"], "Aakash Sharma")
            self.assertEqual(rows[0]["email"], "aakash@example.com")
            self.assertEqual(rows[0]["recommended_package"], "Standard")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
