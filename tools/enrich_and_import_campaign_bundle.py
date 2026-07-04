"""
TOOLS/ENRICH_AND_IMPORT_CAMPAIGN_BUNDLE.PY

Convenience wrapper:
1. Enrich campaign bundle into an output directory.
2. Invoke existing tools/import_campaign_bundle.py with the enriched files.

Run from project root:
    python tools/enrich_and_import_campaign_bundle.py campaigns/sakka \
      --campaign-id sakka \
      --campaign-name "The Chambers of Sakka" \
      --output-dir campaigns/sakka_enriched \
      --clear-rag
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from services.generators.campaign_enricher import CampaignEnricher


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich a campaign bundle and import it using the existing import pipeline.")
    parser.add_argument("input_dir")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--campaign-name", default=None)
    parser.add_argument("--theme", default="ancient cursed dungeon")
    parser.add_argument("--tone", default="grim exploration")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-rooms", type=int, default=None)
    parser.add_argument("--clear-rag", action="store_true")
    args = parser.parse_args()

    enricher = CampaignEnricher()
    outputs = enricher.write_enriched_bundle(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        campaign_id=args.campaign_id,
        campaign_name=args.campaign_name,
        theme=args.theme,
        tone=args.tone,
        max_rooms=args.max_rooms,
    )

    cmd = [
        sys.executable,
        "tools/import_campaign_bundle.py",
        "--campaign-id", args.campaign_id,
        "--name", args.campaign_name or args.campaign_id,
        "--room-data", outputs["room_data"],
        "--room-lookup", outputs["room_lookup"],
        "--rag-index", outputs["rag_index"],
        "--toc-index", outputs["toc_index"],
    ]
    if args.clear_rag:
        cmd.append("--clear-rag")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
