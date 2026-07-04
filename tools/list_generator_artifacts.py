from __future__ import annotations
import argparse, json
from services.generators.artifact_registry import ArtifactRegistry

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--campaign-id'); ap.add_argument('--limit', type=int, default=50); ap.add_argument('--registry', default='campaigns/artifact_registry.jsonl')
    a=ap.parse_args(); rows=ArtifactRegistry(a.registry).list(a.campaign_id, a.limit)
    print(json.dumps([r.to_dict() for r in rows], ensure_ascii=False, indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
