from __future__ import annotations
import argparse,json
from pathlib import Path
from services.movement.movement_state_store import MovementStateStore
from services.movement.visibility_aware_movement_engine import VisibilityAwareMovementEngine

def main()->int:
    p=argparse.ArgumentParser(description='Visibility-aware movement CLI')
    p.add_argument('--bundle-dir',required=True); p.add_argument('--state-file',default=None); p.add_argument('--visibility-state-file',default=None); p.add_argument('--campaign-id',default='tenebrous'); p.add_argument('--start-room',default=None)
    sub=p.add_subparsers(dest='cmd',required=True); sub.add_parser('init').add_argument('--overwrite',action='store_true'); sub.add_parser('look'); sub.add_parser('exits')
    mv=sub.add_parser('move'); mv.add_argument('direction'); mv.add_argument('--choice',type=int,default=None)
    er=sub.add_parser('enter-room'); er.add_argument('room_id'); sub.add_parser('back')
    args=p.parse_args(); bundle=Path(args.bundle_dir); store=MovementStateStore(args.state_file or bundle/'movement_state.json'); engine=VisibilityAwareMovementEngine(bundle,args.visibility_state_file or bundle/'visibility_state.json')
    if args.cmd=='init':
        start=args.start_room or _first_room(bundle); ms=store.init(args.campaign_id,start,overwrite=args.overwrite); vs=engine.init_visibility(args.campaign_id,start,overwrite=args.overwrite)
        print(json.dumps({'movement_state':ms.to_dict(),'visibility_state':vs.to_dict() if vs else None,'visibility_available':engine.visibility_available},ensure_ascii=False,indent=2)); return 0
    ms=store.load()
    if not ms:
        start=args.start_room or _first_room(bundle); ms=store.init(args.campaign_id,start); engine.init_visibility(args.campaign_id,start)
    if args.cmd=='look': out=engine.look(ms)
    elif args.cmd=='exits': out=engine.exits(ms)
    elif args.cmd=='move': out=engine.move(ms,args.direction,args.choice); store.save(ms) if out.get('ok') else None
    elif args.cmd=='enter-room': out=engine.enter_room(ms,args.room_id); store.save(ms) if out.get('ok') else None
    elif args.cmd=='back': out=engine.back(ms); store.save(ms) if out.get('ok') else None
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if out.get('ok',False) else 2

def _first_room(bundle:Path)->str:
    return json.loads((bundle/'room_data.json').read_text(encoding='utf-8'))['rooms'][0]['room_id']
if __name__=='__main__': raise SystemExit(main())
