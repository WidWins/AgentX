from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
LEADS_DIR = BASE_DIR / "data"
LEADS_PATH = LEADS_DIR / "wid_wins_leads.jsonl"
LEADS_CSV_PATH = LEADS_DIR / "wid_wins_leads.csv"
CSV_FIELDNAMES = [
    "captured_at",
    "full_name",
    "email",
    "phone",
    "lead_type",
    "recommended_package",
    "idea_summary",
    "problem",
    "target_users",
    "primary_goal",
    "current_stage",
    "budget",
    "timeline",
    "commitment_level",
    "conversation_summary",
    "notes",
]


def save_lead(payload: dict[str, Any], destination: Path | None = None) -> Path:
    target = destination or LEADS_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    return target



def load_leads(source: Path | None = None) -> list[dict[str, Any]]:
    target = source or LEADS_PATH
    if not target.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records



def export_leads_to_csv(source: Path | None = None, destination: Path | None = None) -> Path:
    source_path = source or LEADS_PATH
    destination_path = destination or LEADS_CSV_PATH
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_leads(source_path)
    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in CSV_FIELDNAMES})

    return destination_path
