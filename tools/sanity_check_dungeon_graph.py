from __future__ import annotations
import argparse,json
from collections import defaultdict,deque
from pathlib import Path

def reach(rooms,edges,undirected=False,include_corridors=True):
    adj=defaultdict(list)
    for e in edges:
        if not include_corridors and e.get('edge_type')=='corridor': continue
        a=e.get('from_room_id'); b=e.get('to_room_id')
        if a in rooms and b in rooms:
            adj[a].append(b)
            if undirected: adj[b].append(a)
    if not rooms: return 0
    start=next(iter(rooms)); seen={start}; q=deque([start])
    while q:
        x=q.popleft()
        for y in adj.get(x,[]):
            if y not in seen: seen.add(y); q.append(y)
    return len(seen)

def main():
    p=argparse.ArgumentParser(); p.add_argument('graph_file'); args=p.parse_args()
    data=json.loads(Path(args.graph_file).read_text(encoding='utf-8'))
    rooms={r['room_id']:r for r in data.get('rooms',[])}; edges=data.get('edges',[])
    missing=[e for e in edges if e.get('from_room_id') not in rooms or e.get('to_room_id') not in rooms]
    by_level=defaultdict(int)
    for r in rooms.values(): by_level[int(r.get('level',0))]+=1
    rep={'rooms':len(rooms),'edges':len(edges),'door_edges':len([e for e in edges if e.get('edge_type')=='door']),'corridor_edges':len([e for e in edges if e.get('edge_type')=='corridor']),'stair_edges':len([e for e in edges if e.get('edge_type')=='stairs']),'missing_target_edges':len(missing),'levels':dict(sorted(by_level.items())),'directed_reachable_no_corridors':reach(rooms,edges,False,False),'directed_reachable_with_corridors':reach(rooms,edges,False,True),'undirected_reachable_with_corridors':reach(rooms,edges,True,True),'warnings':[]}
    if missing: rep['warnings'].append('Some edges reference missing rooms')
    if rep['undirected_reachable_with_corridors'] < max(1,len(rooms)//2): rep['warnings'].append('Undirected reachability is still low; inspect corridor_graph.json and unresolved_doors.json')
    print(json.dumps(rep,ensure_ascii=False,indent=2)); return 1 if missing else 0
if __name__=='__main__': raise SystemExit(main())
