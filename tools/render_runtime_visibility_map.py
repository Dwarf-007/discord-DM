from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.runtime_visibility_map_service import RuntimeVisibilityMapService


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Render channel-specific runtime visibility / fog-of-war map.")
    p.add_argument("--bundle-dir", required=True)
    p.add_argument("--campaign-id", required=True)
    p.add_argument("--channel-id", required=True)
    p.add_argument("--output")
    p.add_argument("--fog-alpha", type=int, default=252)
    p.add_argument("--reveal-padding", type=int, default=0)
    p.add_argument("--draw-cell-outline", action="store_true")
    p.add_argument("--no-current-marker", action="store_true")
    p.add_argument("--vision", default="torch", choices=[
        "none", "darkness", "dim_light", "torch", "lantern", "bullseye_lantern",
        "darkvision_60", "darkvision_120", "daylight",
    ])
    p.add_argument("--bright-radius-cells", type=int)
    p.add_argument("--dim-radius-cells", type=int)
    p.add_argument("--darkvision-radius-cells", type=int)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--viewport", action="store_true", help="Render local cropped viewport. This is the default.")
    mode.add_argument("--full-map", action="store_true", help="Render full level map.")
    p.add_argument("--viewport-radius-cells", type=int, default=25)
    p.add_argument("--crop-padding-pixels", type=int, default=0)
    p.add_argument("--fov-mode", default="true_los", choices=["true_los", "hybrid_corridor", "los_anchor", "legacy"], help="FOV calculation mode. Default: true_los.")
    return p


def main() -> int:
    args = build_parser().parse_args()
    map_mode = "full" if args.full_map else "local"
    service = RuntimeVisibilityMapService(Path(args.bundle_dir), args.campaign_id)
    result = service.render_for_channel(
        args.channel_id,
        output_file=args.output,
        fog_alpha=args.fog_alpha,
        reveal_padding=args.reveal_padding,
        draw_cell_outline=args.draw_cell_outline,
        mark_current_cell=not args.no_current_marker,
        vision_name=args.vision,
        bright_radius_cells=args.bright_radius_cells,
        dim_radius_cells=args.dim_radius_cells,
        darkvision_radius_cells=args.darkvision_radius_cells,
        map_mode=map_mode,
        viewport_radius_cells=args.viewport_radius_cells,
        crop_padding_pixels=args.crop_padding_pixels,
        fov_mode=args.fov_mode,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
