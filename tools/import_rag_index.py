"""
TOOLS/IMPORT_RAG_INDEX.PY
Imports generated rag_index.json into existing rag_chunks + rag_chunks_fts schema.

Input format matches the user's extraction pipeline:
[
  {
    "campaign_id": "MoG",
    "chunk_id": "3",
    "room_id": "graymoor_bend_01",
    "title": "Graymoor Bend",
    "text": "...",
    "tags": [],
    "npc_names": [],
    "monster_names": [],
    "trap_names": [],
    "keyword_hits": []
  }
]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from persistence import database as db
from repositories.rag_chunk_repository import RagChunkRepository


def load_rag_index(path: str) -> List[Dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Nem található rag_index JSON: {path}")
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if isinstance(data.get("chunks"), list):
            return data["chunks"]
        if isinstance(data.get("entries"), list):
            return data["entries"]
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("A rag_index gyökérnek listának vagy objektumnak kell lennie.")


def import_rag_index(json_file: str, default_campaign_id: str = "default", clear_campaign: bool = False) -> int:
    db.initialize_database()
    repo = RagChunkRepository(db)
    repo.ensure_schema()
    chunks = load_rag_index(json_file)

    if clear_campaign:
        repo.delete_campaign_chunks(default_campaign_id)

    count = 0
    for index, chunk in enumerate(chunks, start=1):
        normalized = dict(chunk)
        normalized.setdefault("campaign_id", default_campaign_id)
        normalized.setdefault("chunk_id", str(normalized.get("id") or index))
        repo.upsert_chunk(normalized)
        count += 1
    repo.rebuild_fts(campaign_id=default_campaign_id)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Import generated rag_index.json into rag_chunks schema.")
    parser.add_argument("json_file")
    parser.add_argument("--campaign-id", default="default")
    parser.add_argument("--clear-campaign", action="store_true")
    args = parser.parse_args()
    count = import_rag_index(args.json_file, args.campaign_id, args.clear_campaign)
    print(f"RAG import kész: {count} chunk betöltve a(z) {args.campaign_id} kampányhoz.")


if __name__ == "__main__":
    main()
