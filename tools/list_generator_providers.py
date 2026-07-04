from __future__ import annotations
import argparse, json
from services.generators.provider_registry import build_default_provider_registry

def main():
    ap=argparse.ArgumentParser(description='List generator providers')
    ap.add_argument('--json', action='store_true')
    a=ap.parse_args(); reg=build_default_provider_registry()
    if a.json: print(json.dumps(reg.to_dict(), ensure_ascii=False, indent=2))
    else:
        for p in reg.list(): print(f'{p.provider_id}\t{p.kind}\t{p.name}\t{",".join(p.capabilities)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
