from __future__ import annotations
import argparse,json
from services.dungeons.donjon_tsv_parser import DonjonTsvParser

def main():
    p=argparse.ArgumentParser(); p.add_argument('tsv_file'); args=p.parse_args()
    grid=DonjonTsvParser.parse_file(args.tsv_file)
    print(json.dumps({'rows':grid.n_rows,'cols':grid.n_cols,'tokens':DonjonTsvParser.token_summary(grid)},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
