"""
TOOLS/IMPORT_ROOM_DATA.PY
Imports generated room_data.json into Fixed_Locations via LocationRepository.

Input format:
[
  {
    "room_id": "graymoor_bend_01",
    "title": "Graymoor Bend",
    "room_slug": "graymoor_bend",
    "facts": "...",
    "exits": {},
    "source_chunk_ids": [3, 4]
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


def load_room_data(path: str) -> List[Dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Nem található room_data JSON: {path}")
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if isinstance(data.get("rooms"), list):
            return data["rooms"]
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("A room_data gyökérnek listának vagy objektumnak kell lennie.")


def import_room_data(json_file: str, default_campaign_id: str = "default") -> int:
    db.initialize_database()
    repo = LocationRepository(db)
    rooms = load_room_data(json_file)
    count = 0
    for room in rooms:
        normalized = dict(room)
        normalized.setdefault("campaign_id", default_campaign_id)
        normalized.setdefault("raw", room)
        normalized.setdefault("monsters", room.get("monsters", []))
        repo.upsert_room(normalized)
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Import generated room_data.json into Fixed_Locations.")
    parser.add_argument("json_file")
    parser.add_argument("--campaign-id", default="default")
    args = parser.parse_args()
    count = import_room_data(args.json_file, args.campaign_id)
    print(f"Room import kész: {count} helyszín betöltve a(z) {args.campaign_id} kampányhoz.")


if __name__ == "__main__":
    main()
