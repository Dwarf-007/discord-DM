from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

from services.visibility.donjon_visibility_grid import DonjonVisibilityGrid
from services.visibility.fog_cell_renderer import FogCellRenderer
from services.visibility.fov_anchor import FovAnchorResolver, LOSFovCalculator, CorridorGraphFovCalculator, HybridCorridorLightCalculator
from services.visibility.true_los_visibility_engine import TrueLosVisibilityEngine
from services.visibility.visibility_state_store import VisibilityStateStore
from services.visibility.visible_cell_expander import VisibleCellExpander
from services.visibility.vision_profile import VisionProfiles

Cell = Tuple[int, int]


@dataclass
class RuntimeVisibilityMapResult:
    ok: bool
    message: str
    output_file: Optional[str] = None
    source_map: Optional[str] = None
    level: Optional[int] = None
    map_mode: str = "local"
    visible_cells_count: int = 0
    true_los_cells_count: int = 0
    true_los_candidates_count: int = 0
    true_los_blocked_count: int = 0
    los_cells_count: int = 0
    graph_cells_count: int = 0
    seed_cells_count: int = 0
    hybrid_cells_count: int = 0
    expanded_cells_count: int = 0
    viewport_radius_cells: Optional[int] = 25
    viewport_box: Optional[Dict[str, int]] = None
    vision_profile: Optional[Dict[str, Any]] = None
    fov_anchor: Optional[Dict[str, Any]] = None
    fov_mode: str = "true_los"
    fov_fallback_used: bool = False
    fog_alpha: int = 252
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RuntimeVisibilityMapService:
    """Renders channel-specific FOV/Fog-of-War maps.

    True LOS patch:
    - `true_los` uses supercover line tracing from current anchor.
    - `hybrid_corridor` remains available.
    - `los_anchor` and `legacy` remain diagnostic modes.
    """

    def __init__(self, bundle_dir: str | Path, campaign_id: str) -> None:
        self.bundle_dir = Path(bundle_dir)
        self.campaign_id = str(campaign_id)

    def render_for_channel(
        self,
        channel_id: str,
        *,
        output_file: str | Path | None = None,
        fog_alpha: int = 252,
        reveal_padding: int = 0,
        draw_cell_outline: bool = False,
        mark_current_cell: bool = True,
        vision_name: str = "torch",
        bright_radius_cells: int | None = None,
        dim_radius_cells: int | None = None,
        darkvision_radius_cells: int | None = None,
        map_mode: str = "local",
        viewport_radius_cells: int = 25,
        crop_padding_pixels: int = 0,
        fov_mode: str = "true_los",
    ) -> RuntimeVisibilityMapResult:
        state = VisibilityStateStore(self._state_file(channel_id)).load()
        if not state:
            return RuntimeVisibilityMapResult(False, "Nincs mentett visibility state ehhez a csatornához. Előbb nézz körül vagy lépj egyet.", map_mode=map_mode)

        level = self._current_level(state)
        base_visible_cells = self._visible_cells(state)
        if not base_visible_cells:
            return RuntimeVisibilityMapResult(False, "Nincs látható cella a térkép rendereléséhez.", level=level, map_mode=map_mode, fog_alpha=fog_alpha)

        source_map, cell_size = self._source_map_for_level(level)
        if not source_map:
            return RuntimeVisibilityMapResult(False, f"Nem található player map a(z) {level}. szinthez.", level=level, map_mode=map_mode, fog_alpha=fog_alpha)

        profile = VisionProfiles.build(
            vision_name,
            bright_radius_cells=bright_radius_cells,
            dim_radius_cells=dim_radius_cells,
            darkvision_radius_cells=darkvision_radius_cells,
        )
        grid = self._grid_for_level(level)
        anchor = FovAnchorResolver(self.bundle_dir, grid=grid).resolve(state, base_visible_cells)
        current_cell = (anchor.row, anchor.col) if anchor and mark_current_cell else self._current_cell(state)
        radius = int(max(profile.bright_radius_cells or 0, profile.dim_radius_cells or 0, profile.darkvision_radius_cells or 0))
        mode_key = str(fov_mode or "true_los").lower()
        aliases = {"hybrid": "hybrid_corridor", "anchor": "los_anchor", "supercover": "true_los"}
        mode_key = aliases.get(mode_key, mode_key)
        if mode_key not in {"true_los", "hybrid_corridor", "los_anchor", "legacy"}:
            mode_key = "true_los"

        current = getattr(state, "current", None)
        start_segment_id = getattr(current, "segment_id", None) or getattr(current, "node_id", None)
        true_los_cells: Set[Cell] = set()
        true_los_candidates = 0
        true_los_blocked = 0
        los_cells: Set[Cell] = set()
        graph_cells: Set[Cell] = set()
        seed_cells: Set[Cell] = set()
        hybrid_cells: Set[Cell] = set()
        fallback_used = False
        warning = None

        if anchor and mode_key == "true_los":
            result = TrueLosVisibilityEngine(grid).compute((anchor.row, anchor.col), radius)
            true_los_cells = set(result.visible_cells)
            true_los_candidates = result.candidate_cells_count
            true_los_blocked = result.blocked_rays_count
            expanded_cells = set(true_los_cells)
            if len(expanded_cells) <= 1:
                expanded_cells = set(base_visible_cells)
                fallback_used = True
                warning = "True LOS produced too few cells; fell back to engine visible_cells."
        elif anchor and mode_key == "hybrid_corridor":
            los_cells = LOSFovCalculator(grid).compute((anchor.row, anchor.col), radius)
            graph_cells = CorridorGraphFovCalculator(self.bundle_dir, grid=grid).compute(start_segment_id, (anchor.row, anchor.col), radius, max_hops=2)
            hybrid_calc = HybridCorridorLightCalculator(self.bundle_dir, grid=grid)
            hybrid_cells, seed_cells = hybrid_calc.compute(start_segment_id, (anchor.row, anchor.col), radius, max_graph_hops=2)
            expanded_cells = set(seed_cells) | set(hybrid_cells) | set(graph_cells) | set(los_cells)
            if len(expanded_cells) <= 1:
                expanded_cells = set(base_visible_cells)
                fallback_used = True
                warning = "Hybrid corridor FOV produced too few cells; fell back to engine visible_cells."
        elif anchor and mode_key == "los_anchor":
            los_cells = LOSFovCalculator(grid).compute((anchor.row, anchor.col), radius)
            graph_cells = CorridorGraphFovCalculator(self.bundle_dir, grid=grid).compute(start_segment_id, (anchor.row, anchor.col), radius, max_hops=2)
            expanded_cells = set(los_cells) | set(graph_cells)
            if len(expanded_cells) <= 1:
                expanded_cells = set(base_visible_cells)
                fallback_used = True
                warning = "Anchor/graph FOV produced too few cells; fell back to engine visible_cells."
        else:
            expanded_cells = VisibleCellExpander().expand(base_visible_cells, profile, grid=grid, current_cell=current_cell)
            los_cells = set(expanded_cells)

        if current_cell:
            expanded_cells.add(current_cell)

        mode = "full" if str(map_mode or "").lower() in {"full", "level"} else "local"
        output = Path(output_file) if output_file else self._default_output_file(channel_id, level, mode)
        full_temp = output if mode == "full" else output.with_name(output.stem + "_full_tmp" + output.suffix)

        try:
            rendered = FogCellRenderer().render(
                source_map,
                expanded_cells,
                full_temp,
                cell_size=cell_size,
                fog_alpha=fog_alpha,
                reveal_padding=reveal_padding,
                draw_cell_outline=draw_cell_outline,
                current_cell=current_cell,
            )
            viewport_box = None
            if mode == "local":
                viewport_box = self._crop_viewport(full_temp, output, expanded_cells, cell_size=cell_size, current_cell=current_cell, viewport_radius_cells=viewport_radius_cells, crop_padding_pixels=crop_padding_pixels)
                try:
                    if full_temp != output and full_temp.exists():
                        full_temp.unlink()
                except Exception:
                    pass
                rendered = str(output)
        except Exception as exc:
            return RuntimeVisibilityMapResult(False, f"Nem sikerült a térkép renderelése: {exc}", warning=str(exc))

        return RuntimeVisibilityMapResult(
            ok=True,
            message=f"Térkép elkészült: {rendered}",
            output_file=str(rendered),
            source_map=str(source_map),
            level=level,
            map_mode=mode,
            visible_cells_count=len(base_visible_cells),
            true_los_cells_count=len(true_los_cells),
            true_los_candidates_count=true_los_candidates,
            true_los_blocked_count=true_los_blocked,
            los_cells_count=len(los_cells),
            graph_cells_count=len(graph_cells),
            seed_cells_count=len(seed_cells),
            hybrid_cells_count=len(hybrid_cells),
            expanded_cells_count=len(expanded_cells),
            viewport_radius_cells=viewport_radius_cells if mode == "local" else None,
            viewport_box=viewport_box,
            vision_profile=profile.to_dict(),
            fov_anchor=anchor.to_dict() if anchor else None,
            fov_mode=mode_key,
            fov_fallback_used=fallback_used,
            fog_alpha=fog_alpha,
            warning=warning,
        )

    def _crop_viewport(self, rendered_full_map: Path, output: Path, cells: Set[Cell], *, cell_size: int, current_cell: Optional[Cell], viewport_radius_cells: int, crop_padding_pixels: int = 0) -> Dict[str, int]:
        from PIL import Image
        img = Image.open(rendered_full_map).convert("RGBA")
        radius = max(1, int(viewport_radius_cells or 25))
        center = current_cell or self._centroid_cell(cells) or (0, 0)
        cr, cc = center
        cell = max(1, int(cell_size or 14))
        pad = max(0, int(crop_padding_pixels or 0))
        x0 = max(0, (cc - radius) * cell - pad)
        y0 = max(0, (cr - radius) * cell - pad)
        x1 = min(img.size[0], (cc + radius + 1) * cell + pad)
        y1 = min(img.size[1], (cr + radius + 1) * cell + pad)
        crop = img.crop((int(x0), int(y0), int(x1), int(y1)))
        output.parent.mkdir(parents=True, exist_ok=True)
        crop.save(output)
        return {"x0": int(x0), "y0": int(y0), "x1": int(x1), "y1": int(y1), "width": int(x1 - x0), "height": int(y1 - y0)}

    @staticmethod
    def _centroid_cell(cells: Set[Cell]) -> Optional[Cell]:
        if not cells:
            return None
        return (round(sum(r for r, _ in cells) / len(cells)), round(sum(c for _, c in cells) / len(cells)))

    def _state_file(self, channel_id: str) -> Path:
        safe = str(channel_id).replace("/", "_").replace("\\", "_")
        return self.bundle_dir / f"visibility_runtime_state_{safe}.json"

    def _default_output_file(self, channel_id: str, level: int, mode: str) -> Path:
        safe = str(channel_id).replace("/", "_").replace("\\", "_")
        suffix = "full" if mode == "full" else "view"
        return self.bundle_dir / f"runtime_visibility_map_{safe}_L{int(level):02d}_{suffix}.png"

    def _current_level(self, state: Any) -> int:
        current = getattr(state, "current", None)
        if current and getattr(current, "level", None):
            return int(current.level)
        return 1

    def _current_cell(self, state: Any) -> Optional[Cell]:
        current = getattr(state, "current", None)
        raw = getattr(current, "cell", None) if current else None
        if not raw:
            return None
        try:
            r, c = raw
            return int(r), int(c)
        except Exception:
            return None

    def _visible_cells(self, state: Any) -> Set[Cell]:
        out: Set[Cell] = set()
        for item in getattr(state, "visible_cells", []) or []:
            try:
                r, c = item
                out.add((int(r), int(c)))
            except Exception:
                continue
        return out

    def _grid_for_level(self, level: int) -> Optional[DonjonVisibilityGrid]:
        tsv = self._tsv_for_level(level)
        if not tsv:
            return None
        try:
            return DonjonVisibilityGrid.from_tsv(tsv)
        except Exception:
            return None

    def _tsv_for_level(self, level: int) -> Optional[Path]:
        candidates = []
        for p in self.bundle_dir.rglob("*.tsv"):
            name = p.name.lower()
            score = 0
            if f"l{int(level):02d}" in name or f"level_{int(level):02d}" in str(p).lower():
                score += 10
            if score:
                candidates.append((score, p))
        if candidates:
            candidates.sort(key=lambda x: (-x[0], str(x[1])))
            return candidates[0][1]
        return None

    def _source_map_for_level(self, level: int) -> tuple[Optional[Path], int]:
        cell_size = 14
        for manifest_name in ("fog_manifest.json", "map_geometry.json"):
            data = self._read_json(manifest_name)
            for entry in data.get("levels", []) or []:
                if int(entry.get("level") or entry.get("level_number") or 0) != int(level):
                    continue
                cell_size = int(entry.get("cell_size") or cell_size)
                for key in ("players_map_image", "players_map", "player_map", "map_players"):
                    if entry.get(key):
                        p = self._resolve_path(entry[key])
                        if p.exists():
                            return p, cell_size
        candidates = []
        for p in self.bundle_dir.rglob("*.png"):
            name = p.name.lower()
            score = 0
            if f"l{int(level):02d}" in name or f"level_{int(level):02d}" in str(p).lower():
                score += 10
            if "player" in name:
                score += 5
            if "map" in name:
                score += 2
            if score:
                candidates.append((score, p))
        if candidates:
            candidates.sort(key=lambda x: (-x[0], str(x[1])))
            return candidates[0][1], cell_size
        return None, cell_size

    def _resolve_path(self, value: str | Path) -> Path:
        p = Path(value)
        if p.is_absolute():
            return p
        if p.exists():
            return p
        p2 = self.bundle_dir / p
        if p2.exists():
            return p2
        return p

    def _read_json(self, name: str) -> Dict[str, Any]:
        p = self.bundle_dir / name
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
