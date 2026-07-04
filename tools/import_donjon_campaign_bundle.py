"""
TOOLS/IMPORT_DONJON_CAMPAIGN_BUNDLE.PY

Convenience CLI for Sprint 1 + Sprint 2 in one step:

    python tools/import_donjon_campaign_bundle.py "The Chambers of Sakka the Crimson 01.json" \
      --campaign-id sakka \
      --campaign-name "The Chambers of Sakka the Crimson" \
      --output-dir campaigns/sakka

Requires Sprint 1 files to be present, especially:
    services/generators/donjon_json_importer.py
"""

from __future__ import annotations

import argparse
import json

from services.generators.campaign_bundle_builder import CampaignBundleBuilder
from services.generators.donjon_json_importer import DonjonJsonImporter


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Donjon JSON and write campaign bundle files.")
    parser.add_argument("donjon_json")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--campaign-name", default=None)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    importer = DonjonJsonImporter()
    dungeon = importer.import_file(
        args.donjon_json,
        dungeon_id=args.campaign_id,
        title=args.campaign_name,
    )
    builder = CampaignBundleBuilder()
    outputs = builder.write_bundle(
        generated_dungeon=dungeon,
        campaign_id=args.campaign_id,
        campaign_name=args.campaign_name,
        output_dir=args.output_dir,
    )
    print(json.dumps({"generated": dungeon.summary(), "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
