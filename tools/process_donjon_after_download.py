from __future__ import annotations

import argparse
import json
from services.dungeons.donjon_auto_processing_pipeline import DonjonAutoProcessingPipeline


def main() -> int:
    p = argparse.ArgumentParser(description='Run full Donjon post-download processing pipeline')
    p.add_argument('--campaign-id', required=True)
    p.add_argument('--source-dir', required=True)
    p.add_argument('--output-dir', required=True)
    p.add_argument('--manifest', default=None)
    p.add_argument('--project-root', default='.')
    p.add_argument('--no-copy-assets', action='store_true')
    p.add_argument('--no-sanity-check', action='store_true')
    p.add_argument('--no-secret-state', action='store_true')
    p.add_argument('--max-label-match-distance', type=int, default=2)
    p.add_argument('--runtime-import', action='store_true')
    p.add_argument('--runtime-import-tool', default='tools/import_generated_bundle_runtime.py')
    p.add_argument('--runtime-name', default=None)
    p.add_argument('--clear-rag', action='store_true')
    args = p.parse_args()

    result = DonjonAutoProcessingPipeline(project_root=args.project_root).run(
        campaign_id=args.campaign_id,
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        manifest_file=args.manifest,
        copy_download_assets=not args.no_copy_assets,
        init_secret_state=not args.no_secret_state,
        run_sanity_check=not args.no_sanity_check,
        runtime_import=args.runtime_import,
        runtime_import_tool=args.runtime_import_tool,
        runtime_name=args.runtime_name,
        clear_rag=args.clear_rag,
        max_label_match_distance=args.max_label_match_distance,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 2

if __name__ == '__main__':
    raise SystemExit(main())
