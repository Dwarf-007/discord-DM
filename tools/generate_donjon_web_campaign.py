"""
TOOLS/GENERATE_DONJON_WEB_CAMPAIGN.PY

Sprint 5 CLI:
    python tools/generate_donjon_web_campaign.py sakka \
      --name "The Chambers of Sakka" \
      --theme "Undead" \
      --size "Large" \
      --output-dir campaigns/web/sakka

Requires:
    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import argparse
import json

from services.generators.donjon_web_pipeline import DonjonWebPipeline
from services.generators.web_automation_models import WebGenerationRequest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Donjon dungeon via browser automation and convert it to campaign bundle files.")
    parser.add_argument("campaign_id")
    parser.add_argument("--name", "--campaign-name", dest="campaign_name", default=None)
    parser.add_argument("--url", default="https://donjon.bin.sh/5e/dungeon/")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--seed", default=None)
    parser.add_argument("--theme", default=None)
    parser.add_argument("--size", default=None)
    parser.add_argument("--layout", default=None)
    parser.add_argument("--dungeon-level", default=None)
    parser.add_argument("--party-level", default=None)
    parser.add_argument("--room-layout", default=None)
    parser.add_argument("--room-size", default=None)
    parser.add_argument("--doors", default=None)
    parser.add_argument("--corridor-layout", default=None)
    parser.add_argument("--stairs", default=None)
    parser.add_argument("--map-style", default=None)
    parser.add_argument("--grid", default=None)
    parser.add_argument("--no-enrich", action="store_true")
    parser.add_argument("--max-rooms", type=int, default=None)
    args = parser.parse_args()

    output_dir = args.output_dir or f"campaigns/web/{args.campaign_id}"
    request = WebGenerationRequest(
        campaign_id=args.campaign_id,
        campaign_name=args.campaign_name,
        output_dir=output_dir,
        url=args.url,
        headless=not args.headed,
        seed=args.seed,
        dungeon_name=args.campaign_name,
        theme=args.theme,
        size=args.size,
        layout=args.layout,
        dungeon_level=args.dungeon_level,
        party_level=args.party_level,
        room_layout=args.room_layout,
        room_size=args.room_size,
        doors=args.doors,
        corridor_layout=args.corridor_layout,
        stairs=args.stairs,
        map_style=args.map_style,
        grid=args.grid,
    )
    result = DonjonWebPipeline().generate_campaign_from_web(
        web_request=request,
        enrich=not args.no_enrich,
        max_rooms=args.max_rooms,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
