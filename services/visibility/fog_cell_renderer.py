from __future__ import annotations

from pathlib import Path
from typing import Iterable, Set, Tuple

Cell = Tuple[int, int]
RGBA = Tuple[int, int, int, int]


class FogCellRenderer:
    """Cell szintu fog overlay Donjon player map fole.

    Visible Cell Light Tint Hotfix:
    - a nem latott terulet alapbol teljesen vagy majdnem teljesen fekete;
    - a lathato cellakrol lekerul a fog overlay;
    - a lathato cellak opcionalisan meleg, vilagos tintet kapnak;
    - a tint miatt az eredetileg sotet Donjon PNG cellak is egyertelmuen lathatok;
    - opcionalis cell outline es current-cell marker tovabbra is mukodik.
    """

    def render(
        self,
        source_map: str | Path,
        visible_cells: Iterable[Cell],
        output_file: str | Path,
        cell_size: int = 14,
        *,
        fog_alpha: int = 252,
        reveal_padding: int = 0,
        draw_cell_outline: bool = False,
        current_cell: Cell | None = None,
        visible_tint: bool = True,
        visible_tint_rgba: RGBA = (255, 245, 190, 90),
    ) -> str:
        """Render fog-of-war image.

        Args:
            source_map: Donjon player map PNG path.
            visible_cells: Iterable of (row, col) cells that are currently visible.
            output_file: Output PNG path.
            cell_size: Pixel size of one Donjon grid cell.
            fog_alpha: Alpha value for unseen area. 255 is fully black.
            reveal_padding: Pixel padding around revealed cells.
            draw_cell_outline: Draw a faint outline around visible cells.
            current_cell: Optional current player/party cell marker.
            visible_tint: If true, apply a light tint to visible cells after fog removal.
            visible_tint_rgba: RGBA tint color for visible cells.
        """
        from PIL import Image, ImageDraw

        src = Path(source_map)
        out = Path(output_file)
        img = Image.open(src).convert("RGBA")

        alpha = max(0, min(255, int(fog_alpha)))
        pad = max(0, int(reveal_padding or 0))
        cell = max(1, int(cell_size or 14))

        normalized: Set[Cell] = set()
        for raw in visible_cells:
            try:
                r, c = raw
                normalized.add((int(r), int(c)))
            except Exception:
                continue

        # 1) Apply strict fog overlay everywhere except visible cells.
        overlay = Image.new("RGBA", img.size, (0, 0, 0, alpha))
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)

        for r, c in normalized:
            x0 = max(0, c * cell - pad)
            y0 = max(0, r * cell - pad)
            x1 = min(img.size[0], (c + 1) * cell + pad)
            y1 = min(img.size[1], (r + 1) * cell + pad)
            draw.rectangle([x0, y0, x1, y1], fill=255)

        overlay.putalpha(Image.eval(mask, lambda v: 0 if v else alpha))
        result = Image.alpha_composite(img, overlay)

        # 2) Hotfix: add an explicit light tint to visible cells.
        #    This is intentionally separate from fog removal. A cell can be visible
        #    even if the original Donjon player map pixel underneath is dark.
        if visible_tint and normalized:
            tint_color = self._normalize_rgba(visible_tint_rgba, default=(255, 245, 190, 90))
            tint = Image.new("RGBA", img.size, (0, 0, 0, 0))
            tint_draw = ImageDraw.Draw(tint)
            for r, c in normalized:
                x0 = max(0, c * cell - pad)
                y0 = max(0, r * cell - pad)
                x1 = min(img.size[0], (c + 1) * cell + pad)
                y1 = min(img.size[1], (r + 1) * cell + pad)
                tint_draw.rectangle([x0, y0, x1, y1], fill=tint_color)
            result = Image.alpha_composite(result, tint)

        # 3) Optional debug/user outline for visible cells.
        if draw_cell_outline and normalized:
            outline = ImageDraw.Draw(result)
            for r, c in normalized:
                x0 = c * cell
                y0 = r * cell
                x1 = (c + 1) * cell
                y1 = (r + 1) * cell
                outline.rectangle([x0, y0, x1, y1], outline=(255, 255, 180, 190), width=max(1, cell // 10))

        # 4) Optional current-position marker.
        if current_cell is not None:
            try:
                cr, cc = current_cell
                cr, cc = int(cr), int(cc)
                marker = ImageDraw.Draw(result)
                x0 = cc * cell
                y0 = cr * cell
                x1 = (cc + 1) * cell
                y1 = (cr + 1) * cell
                marker.rectangle([x0, y0, x1, y1], outline=(255, 60, 60, 255), width=max(2, cell // 5))
            except Exception:
                pass

        out.parent.mkdir(parents=True, exist_ok=True)
        result.save(out)
        return str(out)

    @staticmethod
    def _normalize_rgba(value: object, default: RGBA) -> RGBA:
        try:
            if isinstance(value, str):
                parts = [int(p.strip()) for p in value.split(",")]
            else:
                parts = list(value)  # type: ignore[arg-type]
            if len(parts) != 4:
                return default
            r, g, b, a = [max(0, min(255, int(x))) for x in parts]
            return (r, g, b, a)
        except Exception:
            return default
