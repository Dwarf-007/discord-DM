"""
TOOLS/IMPORT_DONJON_JSON.PY

Sprint 1 CLI:
    python tools/import_donjon_json.py input_donjon.json --campaign-id sakka --title "The Chambers of Sakka"

Output:
    generated_dungeon.json

Sprint 2 will add conversion directly into room_data.json / room_lookup.json / rag_index.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.generators.donjon_json_importer import DonjonJsonImporter


def import_donjon_json(input_file: str, campaign_id: str, title: str | None = None, output_file: str = "generated_dungeon.json") -> dict:
    importer = DonjonJsonImporter()
    dungeon = importer.import_file(input_file, dungeon_id=campaign_id, title=title)
    output = Path(output_file)
    output.write_text(json.dumps(dungeon.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output_file": str(output), **dungeon.summary()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Donjon dungeon JSON into GeneratedDungeon intermediate JSON.")
    parser.add_argument("input_file")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--output", default="generated_dungeon.json")
    args = parser.parse_args()

    summary = import_donjon_json(
        input_file=args.input_file,
        campaign_id=args.campaign_id,
        title=args.title,
        output_file=args.output,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
