from __future__ import annotations
import argparse, json
from services.generators.hardened_donjon_web_runner import HardenedDonjonWebRunner
from services.generators.retry_policy import RetryPolicy
try:
    from services.generators.web_automation_models import WebGenerationRequest
except Exception:
    from services.generators.donjon_web_provider_v2 import WebGenerationRequest

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('campaign_id'); ap.add_argument('--name', dest='campaign_name'); ap.add_argument('--output-dir'); ap.add_argument('--theme'); ap.add_argument('--size'); ap.add_argument('--layout'); ap.add_argument('--headed', action='store_true'); ap.add_argument('--refresh-cache', action='store_true'); ap.add_argument('--no-cache', action='store_true'); ap.add_argument('--max-attempts', type=int, default=3); ap.add_argument('--min-interval', type=float, default=10.0)
    a=ap.parse_args(); req=WebGenerationRequest(campaign_id=a.campaign_id, campaign_name=a.campaign_name, output_dir=a.output_dir or f'campaigns/web/{a.campaign_id}', headless=not a.headed, theme=a.theme, size=a.size, layout=a.layout)
    result=HardenedDonjonWebRunner(retry_policy=RetryPolicy(max_attempts=a.max_attempts), min_interval_seconds=a.min_interval).run(req, use_cache=not a.no_cache, refresh_cache=a.refresh_cache)
    print(json.dumps(result.to_dict() if hasattr(result,'to_dict') else str(result), ensure_ascii=False, indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
