
"""
TOOLS/IMPORT_CAMPAIGN_BUNDLE.PY
Imports generated campaign bundle files, including scenes/progress seed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from persistence import database as db
from repositories.campaign_repository import CampaignRepository
from repositories.channel_repository import ChannelRepository
from repositories.campaign_progress_repository import CampaignProgressRepository
from repositories.location_repository import LocationRepository
from repositories.rag_chunk_repository import RagChunkRepository
from repositories.room_alias_repository import RoomAliasRepository
from services.progress_service import ProgressService


def read_json_if_exists(path: str | None) -> Optional[Any]:
    if not path:
        return None
    source = Path(path)
    if not source.exists():
        return None
    return json.loads(source.read_text(encoding="utf-8"))


def as_list(data: Any, key: str) -> list[Dict[str, Any]]:
    if data is None:
        return []
    if isinstance(data, list):
        return [dict(item) for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get(key), list):
        return [dict(item) for item in data[key] if isinstance(item, dict)]
    if isinstance(data, dict):
        return [dict(data)]
    return []


def import_campaign_bundle(
    campaign_id: str,
    name: str | None = None,
    description: str = "",
    rag_index_path: str = "rag_index.json",
    room_data_path: str = "room_data.json",
    room_lookup_path: str = "room_lookup.json",
    toc_index_path: str = "toc_index.json",
    clear_rag: bool = False,
) -> dict[str, int]:
    db.initialize_database()
    campaign_repo = CampaignRepository(db)
    location_repo = LocationRepository(db)
    rag_repo = RagChunkRepository(db)
    alias_repo = RoomAliasRepository(db)
    progress_repo = CampaignProgressRepository(db)
    channel_repo = ChannelRepository(db)
    campaign_repo.ensure_schema()
    rag_repo.ensure_schema()
    alias_repo.ensure_schema()
    progress_repo.ensure_schema()

    room_lookup = read_json_if_exists(room_lookup_path) or {}
    toc_index = read_json_if_exists(toc_index_path) or {}
    metadata = {
        "room_lookup_count": len(room_lookup) if isinstance(room_lookup, dict) else 0,
        "toc_entries": len(toc_index.get("entries", [])) if isinstance(toc_index, dict) else 0,
    }
    campaign_repo.upsert_campaign(campaign_id, name=name or campaign_id, description=description, metadata=metadata)

    room_data = as_list(read_json_if_exists(room_data_path), "rooms")
    room_count = 0
    for room in room_data:
        normalized = dict(room)
        normalized.setdefault("campaign_id", campaign_id)
        normalized.setdefault("raw", room)
        normalized.setdefault("monsters", room.get("monsters", []))
        location_repo.upsert_room(normalized)
        room_id = str(normalized.get("room_id") or "").strip()
        title = str(normalized.get("title") or "").strip()
        slug = str(normalized.get("room_slug") or normalized.get("slug") or "").strip()
        if room_id:
            alias_repo.upsert_alias(campaign_id, room_id, room_id, title=title or None, source="room_data")
            if title:
                alias_repo.upsert_alias(campaign_id, title, room_id, title=title, source="room_data")
            if slug:
                alias_repo.upsert_alias(campaign_id, slug, room_id, title=title or None, source="room_data")
        room_count += 1

    alias_count = alias_repo.import_lookup(campaign_id, room_lookup, source=room_lookup_path) if isinstance(room_lookup, dict) else 0

    if clear_rag:
        rag_repo.delete_campaign_chunks(campaign_id)
    rag_count = 0
    for chunk in as_list(read_json_if_exists(rag_index_path), "chunks"):
        normalized = dict(chunk)
        normalized.setdefault("campaign_id", campaign_id)
        rag_repo.upsert_chunk(normalized)
        rag_count += 1
    rag_repo.rebuild_fts(campaign_id=campaign_id)

    progress_service = ProgressService(progress_repo, channel_repo)
    toc_scene_count = progress_service.import_toc_entries(campaign_id, toc_index if isinstance(toc_index, dict) else {})
    room_scene_count = progress_service.ensure_scenes_from_rooms(campaign_id, room_data) if toc_scene_count == 0 else 0

    return {
        "rooms": room_count,
        "rag_chunks": rag_count,
        "aliases": alias_count,
        "toc_scenes": toc_scene_count,
        "room_scenes": room_scene_count,
        "campaigns": 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import generated campaign bundle files.")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--name", default=None)
    parser.add_argument("--description", default="")
    parser.add_argument("--rag-index", default="rag_index.json")
    parser.add_argument("--room-data", default="room_data.json")
    parser.add_argument("--room-lookup", default="room_lookup.json")
    parser.add_argument("--toc-index", default="toc_index.json")
    parser.add_argument("--clear-rag", action="store_true")
    args = parser.parse_args()
    result = import_campaign_bundle(
        campaign_id=args.campaign_id,
        name=args.name,
        description=args.description,
        rag_index_path=args.rag_index,
        room_data_path=args.room_data,
        room_lookup_path=args.room_lookup,
        toc_index_path=args.toc_index,
        clear_rag=args.clear_rag,
    )
    print(f"Campaign import kész: {result}")


if __name__ == "__main__":
    main()
