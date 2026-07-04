"""
TOOLS/INSPECT_RAG_DB.PY
Inspects rag_chunks and rag_chunks_fts table status.

Run:
    python tools/inspect_rag_db.py --campaign-id MoG
"""

from __future__ import annotations

import argparse

from persistence import database as db
from repositories.rag_chunk_repository import RagChunkRepository


def inspect(campaign_id: str | None = None) -> None:
    repo = RagChunkRepository(db)
    repo.ensure_schema()
    chunks = repo.list_chunks(campaign_id=campaign_id, limit=10000)
    room_count = len({chunk.room_id for chunk in chunks if chunk.room_id})
    print(f"Chunks: {len(chunks)}")
    print(f"Rooms linked: {room_count}")
    if chunks:
        print("First chunks:")
        for chunk in chunks[:5]:
            print(f"- id={chunk.id} campaign={chunk.campaign_id} chunk={chunk.chunk_id} room={chunk.room_id} title={chunk.title}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect RAG DB tables.")
    parser.add_argument("--campaign-id", default=None)
    args = parser.parse_args()
    inspect(args.campaign_id)


if __name__ == "__main__":
    main()
