"""
TOOLS/BUILD_CAMPAIGN_BUNDLE_FROM_GENERATED.PY

Sprint 2 CLI:
    python tools/build_campaign_bundle_from_generated.py generated_dungeon.json --campaign-id sakka --output-dir campaigns/sakka

This writes:
    campaigns/sakka/room_data.json
    campaigns/sakka/room_lookup.json
    campaigns/sakka/rag_index.json
    campaigns/sakka/toc_index.json
    campaigns/sakka/campaign_bundle_manifest.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.generators.campaign_bundle_builder import CampaignBundleBuilder


def build_campaign_bundle_from_generated(
    generated_file: str,
    campaign_id: str,
    output_dir: str,
    campaign_name: str | None = None,
) -> dict:
    data = json.loads(Path(generated_file).read_text(encoding="utf-8"))
    builder = CampaignBundleBuilder()
    outputs = builder.write_bundle(
        generated_dungeon=data,
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        output_dir=output_dir,
    )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build existing campaign bundle JSON files from generated_dungeon.json.")
    parser.add_argument("generated_file")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--campaign-name", default=None)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    outputs = build_campaign_bundle_from_generated(
        generated_file=args.generated_file,
        campaign_id=args.campaign_id,
        campaign_name=args.campaign_name,
        output_dir=args.output_dir,
    )
    print(json.dumps(outputs, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
