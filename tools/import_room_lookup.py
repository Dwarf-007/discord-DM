
"""
TOOLS/IMPORT_ROOM_LOOKUP.PY
Imports generated room_lookup.json into Room_Aliases.

Run:
    python tools/import_room_lookup.py room_lookup.json --campaign-id MoG
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from persistence import database as db
from repositories.room_alias_repository import RoomAliasRepository


def import_room_lookup(path: str, campaign_id: str) -> int:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Nem található room_lookup JSON: {path}")
    lookup = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(lookup, dict):
        raise ValueError("A room_lookup gyökérnek objektumnak kell lennie.")
    db.initialize_database()
    repo = RoomAliasRepository(db)
    return repo.import_lookup(campaign_id, lookup)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import generated room_lookup.json into Room_Aliases.")
    parser.add_argument("json_file")
    parser.add_argument("--campaign-id", required=True)
    args = parser.parse_args()
    count = import_room_lookup(args.json_file, args.campaign_id)
    print(f"Room lookup import kész: {count} lookup bejegyzés feldolgozva.")


if __name__ == "__main__":
    main()
