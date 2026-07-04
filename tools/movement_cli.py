from __future__ import annotations
import argparse
import json
from pathlib import Path

from services.movement.navigation_repository import NavigationRepository
from services.movement.movement_engine import MovementEngine
from services.movement.movement_map_service import MovementMapService
from services.movement.movement_state_store import MovementStateStore


def main() -> int:
    parser = argparse.ArgumentParser(description='AI DM movement engine CLI')
    parser.add_argument('--bundle-dir', required=True)
    parser.add_argument('--state-file', default=None)
    parser.add_argument('--campaign-id', default='tenebrous')
    parser.add_argument('--start-room', default=None)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init').add_argument('--overwrite', action='store_true')
    sub.add_parser('look')
    sub.add_parser('exits')
    mv = sub.add_parser('move'); mv.add_argument('direction'); mv.add_argument('--choice', type=int, default=None)
    sub.add_parser('back')
    gt = sub.add_parser('goto'); gt.add_argument('room')
    mp = sub.add_parser('map'); mp.add_argument('--output', default=None); mp.add_argument('--no-adjacent', action='store_true')
    args = parser.parse_args()

    bundle = Path(args.bundle_dir)
    state_file = Path(args.state_file) if args.state_file else bundle / 'movement_state.json'
    store = MovementStateStore(state_file)
    repo = NavigationRepository(bundle)
    engine = MovementEngine(repo)

    if args.cmd == 'init':
        start = args.start_room or _first_room(bundle)
        state = store.init(args.campaign_id, start, overwrite=args.overwrite)
        print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2))
        return 0

    state = store.load()
    if not state:
        start = args.start_room or _first_room(bundle)
        state = store.init(args.campaign_id, start, overwrite=False)

    if args.cmd == 'look':
        result = engine.look(state)
    elif args.cmd == 'exits':
        result = engine.exits(state)
    elif args.cmd == 'move':
        result = engine.move(state, args.direction, choice=args.choice)
        if result.ok:
            store.save(result.state)
    elif args.cmd == 'back':
        result = engine.back(state)
        if result.ok:
            store.save(result.state)
    elif args.cmd == 'goto':
        result = engine.goto(state, args.room)
        if result.ok:
            store.save(result.state)
    elif args.cmd == 'map':
        map_file = MovementMapService(bundle).render_map(state, show_adjacent=not args.no_adjacent, output_file=args.output)
        result = engine.look(state)
        result.map_file = map_file
    else:
        raise RuntimeError(args.cmd)

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.message:
        print('\n---\n' + result.message)
    return 0 if result.ok else 2


def _first_room(bundle: Path) -> str:
    data = json.loads((bundle / 'room_data.json').read_text(encoding='utf-8'))
    rooms = data.get('rooms') or []
    if not rooms:
        raise SystemExit('room_data.json contains no rooms')
    return rooms[0]['room_id']

if __name__ == '__main__':
    raise SystemExit(main())
