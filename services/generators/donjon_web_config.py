"""
SERVICES/GENERATORS/DONJON_WEB_CONFIG.PY

Selector configuration for Donjon browser automation.

Important:
Donjon is an external website and can change without notice. Therefore selectors
are configurable and multiple fallback selectors are tried.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class DonjonWebSelectors:
    generate_button: List[str] = field(default_factory=lambda: [
        "input[type=submit][value*=Construct]",
        "input[type=submit][value*=Generate]",
        "button:has-text('Construct')",
        "button:has-text('Generate')",
        "input[type=submit]",
    ])
    json_links: List[str] = field(default_factory=lambda: [
        "a[href$='.json']",
        "a:has-text('JSON')",
        "a:has-text('json')",
        "a[href*='json']",
    ])
    pdf_links: List[str] = field(default_factory=lambda: [
        "a[href$='.pdf']",
        "a:has-text('PDF')",
        "a:has-text('pdf')",
        "a[href*='pdf']",
    ])
    form_fields: Dict[str, List[str]] = field(default_factory=lambda: {
        "seed": ["input[name='seed']", "#seed"],
        "dungeon_name": ["input[name='dungeon_name']", "input[name='name']", "#dungeon_name", "#name"],
        "dungeon_level": ["select[name='dungeon_level']", "select[name='level']", "input[name='level']"],
        "party_level": ["select[name='party_level']", "select[name='party']", "input[name='party_level']"],
        "size": ["select[name='size']", "select[name='dungeon_size']", "#size"],
        "layout": ["select[name='layout']", "select[name='dungeon_layout']", "#layout"],
        "theme": ["select[name='theme']", "input[name='theme']", "#theme"],
        "peripheral_egress": ["select[name='peripheral_egress']", "#peripheral_egress"],
        "room_layout": ["select[name='room_layout']", "#room_layout"],
        "room_size": ["select[name='room_size']", "#room_size"],
        "doors": ["select[name='doors']", "#doors"],
        "corridor_layout": ["select[name='corridor_layout']", "#corridor_layout"],
        "remove_deadends": ["select[name='remove_deadends']", "#remove_deadends"],
        "stairs": ["select[name='stairs']", "#stairs"],
        "map_style": ["select[name='map_style']", "#map_style"],
        "grid": ["select[name='grid']", "#grid"],
    })

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_file(cls, path: str | Path) -> "DonjonWebSelectors":
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls(
            generate_button=list(data.get("generate_button", cls().generate_button)),
            json_links=list(data.get("json_links", cls().json_links)),
            pdf_links=list(data.get("pdf_links", cls().pdf_links)),
            form_fields=dict(data.get("form_fields", cls().form_fields)),
        )
