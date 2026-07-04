from __future__ import annotations
import argparse, json
from services.generators.donjon_web_provider_v2 import DonjonWebProviderV2, WebGenerationRequest

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('campaign_id'); ap.add_argument('--name', dest='campaign_name'); ap.add_argument('--url', default='https://donjon.bin.sh/5e/dungeon/'); ap.add_argument('--output-dir'); ap.add_argument('--headed', action='store_true'); ap.add_argument('--refresh-cache', action='store_true'); ap.add_argument('--no-cache', action='store_true'); ap.add_argument('--theme'); ap.add_argument('--size'); ap.add_argument('--layout')
    a=ap.parse_args(); req=WebGenerationRequest(campaign_id=a.campaign_id, campaign_name=a.campaign_name, output_dir=a.output_dir or f'campaigns/web/{a.campaign_id}', url=a.url, headless=not a.headed, theme=a.theme, size=a.size, layout=a.layout)
    res=DonjonWebProviderV2().generate(req, use_cache=not a.no_cache, refresh_cache=a.refresh_cache)
    print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
