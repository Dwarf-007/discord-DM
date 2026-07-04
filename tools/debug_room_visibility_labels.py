from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description='Debug player-safe and DM labels for one room')
    p.add_argument('--bundle-dir', required=True)
    p.add_argument('--room', required=True)
    p.add_argument('--show-dm', action='store_true')
    args = p.parse_args()
    path = Path(args.bundle_dir) / 'corridor_visibility_labels.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    exits = data.get('room_exits', {}).get(args.room, [])
    if not args.show_dm:
        exits = [
            {
                'segment_id': e.get('segment_id'),
                'direction': e.get('direction'),
                'player_label': e.get('player_label') or e.get('label'),
                'player_description': e.get('player_description') or e.get('description'),
                'hidden_traits': e.get('hidden_traits', []),
                'requires_detection': e.get('requires_detection', False),
                'target_room_id': e.get('target_room_id'),
            }
            for e in exits
        ]
    print(json.dumps({'room_id': args.room, 'exit_count': len(exits), 'exits': exits}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
