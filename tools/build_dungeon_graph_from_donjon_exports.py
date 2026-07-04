from __future__ import annotations
import argparse, json
from services.dungeons.donjon_graph_builder import DonjonGraphBuilder
from services.dungeons.dungeon_bundle_exporter import DungeonBundleExporter

def main()->int:
    p=argparse.ArgumentParser(description='Build DungeonGraph v3 with TSV corridor connectivity')
    p.add_argument('--campaign-id',required=True); p.add_argument('--dungeon-id'); p.add_argument('--title'); p.add_argument('--manifest',required=True); p.add_argument('--output-dir',required=True); p.add_argument('--no-tsv-corridors',action='store_true')
    args=p.parse_args()
    graph=DonjonGraphBuilder(args.campaign_id,args.dungeon_id or args.campaign_id,args.title or args.dungeon_id or args.campaign_id,enable_tsv_corridors=not args.no_tsv_corridors).build_from_manifest(args.manifest)
    files=DungeonBundleExporter().export(graph,args.output_dir)
    print(json.dumps({'status':'OK','rooms':len(graph.rooms),'edges':len(graph.edges),'door_edges':len([e for e in graph.edges if e.edge_type=='door']),'corridor_edges':len([e for e in graph.edges if e.edge_type=='corridor']),'stairs':len(graph.stairs),'stair_edges':len([e for e in graph.edges if e.edge_type=='stairs']),'levels':len(graph.levels),'files':files,'warnings':graph.metadata.get('warnings',[]),'tsv_corridor_reports':graph.metadata.get('tsv_corridor_reports',[])},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
