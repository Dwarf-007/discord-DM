"""
TOOLS/GENERATE_CAMPAIGN.PY

Sprint 4 CLI for generation orchestration.

Examples:
    python tools/generate_campaign.py donjon_json sakka ./sakka.json \
      --name "The Chambers of Sakka" \
      --theme "lich-haunted crimson dungeon" \
      --output-dir campaigns/sakka

    python tools/generate_campaign.py sakka ./sakka.json --no-enrich
"""

from __future__ import annotations

import argparse
import json

from services.generators.generation_orchestrator import GenerateCampaignRequest, GenerationOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a campaign bundle from a supported procedural source.")
    parser.add_argument("provider_or_campaign_id")
    parser.add_argument("campaign_id_or_source")
    parser.add_argument("source_path", nargs="?")
    parser.add_argument("--name", "--campaign-name", dest="campaign_name", default=None)
    parser.add_argument("--theme", default="ancient cursed dungeon")
    parser.add_argument("--tone", default="grim exploration")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--no-enrich", action="store_true")
    parser.add_argument("--max-rooms", type=int, default=None)
    args = parser.parse_args()

    if args.source_path is None:
        provider = "donjon_json"
        campaign_id = args.provider_or_campaign_id
        source_path = args.campaign_id_or_source
    else:
        provider = args.provider_or_campaign_id
        campaign_id = args.campaign_id_or_source
        source_path = args.source_path

    output_dir = args.output_dir or f"campaigns/{campaign_id}"
    request = GenerateCampaignRequest(
        campaign_id=campaign_id,
        campaign_name=args.campaign_name,
        provider=provider,
        source_path=source_path,
        output_dir=output_dir,
        theme=args.theme,
        tone=args.tone,
        enrich=not args.no_enrich,
        max_rooms=args.max_rooms,
    )
    result = GenerationOrchestrator().generate_campaign(request)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
