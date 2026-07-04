"""
TOOLS/DB_JSON_IMPORTER.PY
Imports structured campaign room JSON into SQLite Fixed_Locations.

Expected JSON input examples:
[
  {
    "room_id": "room_1",
    "campaign_id": "lost_mines",
    "title": "Cave Entrance",
    "facts": "...",
    "exits": {"north": "room_2"},
    "monsters": [{"name": "Goblin", "count": 2}]
  }
]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from persistence import database as db
from repositories.location_repository import LocationRepository


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"A megadott JSON import fájl nem található: {file_path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if "rooms" in data and isinstance(data["rooms"], list):
            return data["rooms"]
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("A JSON gyökérnek listának vagy objektumnak kell lennie.")


def import_campaign_data_from_json(json_filename: str, default_campaign_id: str = "default") -> int:
    db.initialize_database()
    repo = LocationRepository(db)
    rooms = load_json_file(json_filename)

    imported = 0
    for room in rooms:
        normalized = dict(room)
        normalized.setdefault("campaign_id", default_campaign_id)
        repo.upsert_room(normalized)
        imported += 1

    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Import campaign room JSON into SQLite.")
    parser.add_argument("json_file", help="Path to JSON file")
    parser.add_argument("--campaign-id", default="default", help="Default campaign_id if missing")
    args = parser.parse_args()

    count = import_campaign_data_from_json(args.json_file, args.campaign_id)
    print(f"Import kész: {count} szoba/helyszín betöltve.")


if __name__ == "__main__":
    main()
