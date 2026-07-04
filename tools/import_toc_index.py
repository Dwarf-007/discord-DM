
"""
TOOLS/IMPORT_TOC_INDEX.PY
Imports toc_index.json into Campaign_Scenes.

The current toc_index.json may be empty; this importer is still useful once the
TOC extraction produces entries.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from persistence import database as db
from repositories.campaign_progress_repository import CampaignProgressRepository
from repositories.channel_repository import ChannelRepository
from services.progress_service import ProgressService


def import_toc_index(path: str, campaign_id: str) -> int:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Nem található toc_index JSON: {path}")
    toc_data = json.loads(source.read_text(encoding="utf-8"))
    db.initialize_database()
    repo = CampaignProgressRepository(db)
    channel_repo = ChannelRepository(db)
    service = ProgressService(repo, channel_repo)
    return service.import_toc_entries(campaign_id, toc_data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import toc_index.json into Campaign_Scenes.")
    parser.add_argument("json_file")
    parser.add_argument("--campaign-id", required=True)
    args = parser.parse_args()
    count = import_toc_index(args.json_file, args.campaign_id)
    print(f"TOC import kész: {count} scene betöltve.")


if __name__ == "__main__":
    main()
