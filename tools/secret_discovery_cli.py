from __future__ import annotations
import argparse
import json
from pathlib import Path

from services.visibility.secret_door_discovery_engine import SecretDoorDiscoveryEngine


def main() -> int:
    p = argparse.ArgumentParser(description='Secret Door Discovery Engine CLI')
    p.add_argument('--bundle-dir', required=True)
    p.add_argument('--state-file', default=None)
    p.add_argument('--campaign-id', default='tenebrous')
    p.add_argument('--scope-id', default='party')
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('init').add_argument('--overwrite', action='store_true')

    sr = sub.add_parser('search-room')
    sr.add_argument('--room', required=True)
    sr.add_argument('--trait', default='secret')
    sr.add_argument('--roll-total', type=int, default=None)
    sr.add_argument('--dc', type=int, default=15)
    sr.add_argument('--auto-success', action='store_true')

    rv = sub.add_parser('reveal-segment')
    rv.add_argument('--segment-id', required=True)
    rv.add_argument('--trait', default='secret')

    ls = sub.add_parser('list-room-secrets')
    ls.add_argument('--room', required=True)

    args = p.parse_args()
    bundle = Path(args.bundle_dir)
    engine = SecretDoorDiscoveryEngine(bundle, state_file=args.state_file or (bundle / 'secret_discovery_state.json'))

    if args.cmd == 'init':
        state = engine.init_state(args.campaign_id, args.scope_id, overwrite=args.overwrite)
        print(json.dumps({'ok': True, 'state': state.to_dict()}, ensure_ascii=False, indent=2))
        return 0

    state = engine.load_or_init_state(args.campaign_id, args.scope_id)

    if args.cmd == 'search-room':
        result = engine.search_room(args.room, state, trait=args.trait, roll_total=args.roll_total, dc=args.dc, auto_success=args.auto_success)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0 if result.ok else 2

    if args.cmd == 'reveal-segment':
        result = engine.reveal_segment(args.segment_id, state, trait=args.trait, reason='manual_cli')
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0 if result.ok else 2

    if args.cmd == 'list-room-secrets':
        secrets = engine.secret_segments_for_room(args.room)
        print(json.dumps({'room_id': args.room, 'secret_count': len(secrets), 'secrets': secrets}, ensure_ascii=False, indent=2))
        return 0

    raise RuntimeError(args.cmd)

if __name__ == '__main__':
    raise SystemExit(main())
