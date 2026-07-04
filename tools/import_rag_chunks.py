"""
TOOLS/IMPORT_RAG_CHUNKS.PY
Imports campaign RAG chunks from JSON into SQLite.

Accepted JSON shapes:

1. List of chunks:
[
  {"chunk_id":"c1", "campaign_id":"lost_mines", "room_id":"room_1", "text":"..."}
]

2. Object with chunks key:
{"chunks": [...]}

Run:
    python tools/import_rag_chunks.py chunks.json --campaign-id lost_mines
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from persistence import database as db
from repositories.rag_chunk_repository import RagChunkRepository


def load_chunks(path: str) -> List[Dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Nem található JSON fájl: {path}")
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if isinstance(data.get("chunks"), list):
            return data["chunks"]
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("A JSON gyökérnek listának vagy objektumnak kell lennie.")


def import_chunks(json_file: str, default_campaign_id: str = "default") -> int:
    db.initialize_database()
    repo = RagChunkRepository(db)
    repo.ensure_schema()
    chunks = load_chunks(json_file)

    count = 0
    for index, chunk in enumerate(chunks, start=1):
        normalized = dict(chunk)
        normalized.setdefault("campaign_id", default_campaign_id)
        normalized.setdefault("chunk_id", normalized.get("id") or f"{default_campaign_id}_chunk_{index}")
        repo.upsert_chunk(normalized)
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Import RAG chunks into SQLite.")
    parser.add_argument("json_file")
    parser.add_argument("--campaign-id", default="default")
    args = parser.parse_args()
    count = import_chunks(args.json_file, args.campaign_id)
    print(f"RAG import kész: {count} chunk betöltve.")


if __name__ == "__main__":
    main()
