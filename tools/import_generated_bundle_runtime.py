"""
TOOLS/IMPORT_GENERATED_BUNDLE_RUNTIME.PY

Imports a generated Sprint 2-4 campaign bundle using the uploaded older runtime
branch's repositories/services. This is useful after:

    python tools/generate_campaign.py donjon_json sakka ./sakka.json --output-dir campaigns/sakka

Then:

    python tools/import_generated_bundle_runtime.py campaigns/sakka/bundle --campaign-id sakka --name "Sakka" --clear-rag
"""
from __future__ import annotations

import argparse
from app.bootstrap import build_runtime
from services.generators.legacy_runtime_adapter import LegacyRuntimeGeneratorAdapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Import generated campaign bundle through runtime services.")
    parser.add_argument("bundle_dir")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--name", default=None)
    parser.add_argument("--clear-rag", action="store_true")
    args = parser.parse_args()
    runtime = build_runtime()
    result = LegacyRuntimeGeneratorAdapter(runtime).import_bundle_dir(
        campaign_id=args.campaign_id,
        campaign_name=args.name or args.campaign_id,
        bundle_dir=args.bundle_dir,
        clear_rag=args.clear_rag,
    )
    print(f"Import kész: rooms={result['rooms']} aliases={result['aliases']} chunks={result['chunks']} scenes={result['scenes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
