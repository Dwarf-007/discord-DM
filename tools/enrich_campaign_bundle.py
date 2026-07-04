"""
TOOLS/ENRICH_CAMPAIGN_BUNDLE.PY

Sprint 3 CLI:
    python tools/enrich_campaign_bundle.py campaigns/sakka \
      --campaign-id sakka \
      --campaign-name "The Chambers of Sakka" \
      --theme "lich-haunted crimson dungeon" \
      --output-dir campaigns/sakka_enriched

By default this uses deterministic enrichment. Add --use-llm only when wiring an
LLM adapter in a custom integration.
"""

from __future__ import annotations

import argparse
import json

from services.generators.campaign_enricher import CampaignEnricher


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich a generated campaign bundle with deterministic/optional-LLM lore and room text.")
    parser.add_argument("input_dir")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--campaign-name", default=None)
    parser.add_argument("--theme", default="ancient cursed dungeon")
    parser.add_argument("--tone", default="grim exploration")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-rooms", type=int, default=None)
    parser.add_argument("--use-llm", action="store_true", help="Reserved for integrations that inject an LLM adapter.")
    args = parser.parse_args()

    enricher = CampaignEnricher(llm_adapter=None)
    outputs = enricher.write_enriched_bundle(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        campaign_id=args.campaign_id,
        campaign_name=args.campaign_name,
        theme=args.theme,
        tone=args.tone,
        use_llm=False,
        max_rooms=args.max_rooms,
    )
    print(json.dumps(outputs, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
