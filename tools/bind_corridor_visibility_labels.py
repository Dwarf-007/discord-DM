from __future__ import annotations
import argparse
import json
from services.visibility.door_metadata_binder import CorridorVisibilityDoorMetadataBinder


def main() -> int:
    p = argparse.ArgumentParser(description='Bind Donjon door metadata to corridor visibility segments')
    p.add_argument('--bundle-dir', required=True)
    p.add_argument('--max-match-distance', type=int, default=2)
    args = p.parse_args()
    data = CorridorVisibilityDoorMetadataBinder(
        args.bundle_dir,
        max_match_distance=args.max_match_distance,
    ).build_and_save()
    print(json.dumps({
        'status': 'OK',
        'file': f"{args.bundle_dir.rstrip('/')}/corridor_visibility_labels.json",
        'stats': data.get('stats', {}),
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
