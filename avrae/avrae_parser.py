"""
AVRAE/AVRAE_PARSER.PY
Parser utilities for Avrae Discord messages and embeds.

This is intentionally heuristic: Avrae message formats can vary. The parser
extracts useful signals without becoming a second combat rules engine.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Tuple


class AvraeParserService:
    @staticmethod
    def extract_full_text(message_or_embeds) -> str:
        if hasattr(message_or_embeds, "content"):
            content = message_or_embeds.content or ""
            embeds = getattr(message_or_embeds, "embeds", []) or []
            return (content + "\n" + AvraeParserService.extract_full_text(embeds)).strip()

        embeds = message_or_embeds or []
        if not isinstance(embeds, list):
            embeds = [embeds]

        fragments: List[str] = []
        for embed in embeds:
            fragments.append(str(getattr(embed, "title", "") or ""))
            fragments.append(str(getattr(embed, "description", "") or ""))
            author = getattr(embed, "author", None)
            fragments.append(str(getattr(author, "name", "") or ""))
            for field in getattr(embed, "fields", []) or []:
                fragments.append(str(getattr(field, "name", "") or ""))
                fragments.append(str(getattr(field, "value", "") or ""))
        return "\n".join(part for part in fragments if part).strip()

    @staticmethod
    def is_avrae_message(message) -> bool:
        author = getattr(message, "author", None)
        name = str(getattr(author, "name", "") or "").lower()
        display_name = str(getattr(author, "display_name", "") or "").lower()
        return "avrae" in name or "avrae" in display_name

    @staticmethod
    def is_combat_trigger(text: str) -> bool:
        lower = (text or "").lower()
        return any(keyword in lower for keyword in ["initiative", "combat", "kezdeményezés", "init"])

    @staticmethod
    def is_hp_update(text: str) -> bool:
        lower = (text or "").lower()
        return "hp:" in lower or "hit points" in lower or "❤️" in text

    @staticmethod
    def is_death_event(text: str) -> bool:
        lower = (text or "").lower()
        return any(keyword in lower for keyword in ["dead", "dying", "defeated", "killed", "0 hp"])

    @staticmethod
    def extract_defeated_names(text: str) -> List[str]:
        """
        Heuristic extraction of defeated monster names from Avrae-like text.

        Supported patterns include examples like:
        - "Goblin is dead"
        - "Goblin defeated"
        - "Killed: Goblin"
        - "Goblin drops to 0 HP"
        """

        if not text:
            return []

        patterns = [
            r"(?im)^\s*(?P<name>[A-Za-z][A-Za-z0-9_ '\-]{1,60})\s+(?:is\s+)?(?:dead|defeated|killed)\b",
            r"(?im)\b(?:dead|defeated|killed)\s*[:\-]\s*(?P<name>[A-Za-z][A-Za-z0-9_ '\-]{1,60})",
            r"(?im)^\s*(?P<name>[A-Za-z][A-Za-z0-9_ '\-]{1,60})\s+(?:drops|falls)\s+to\s+0\s*hp\b",
        ]

        names: List[str] = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                name = AvraeParserService._clean_name(match.group("name"))
                if name and name.lower() not in {n.lower() for n in names}:
                    names.append(name)
        return names

    @staticmethod
    def extract_total_roll(text: str) -> Optional[int]:
        match = re.search(r"=\s*(\d+)", text or "")
        if match:
            return int(match.group(1))
        numbers = re.findall(r"\b\d+\b", text or "")
        if numbers:
            return int(numbers[-1])
        return None

    @staticmethod
    def evaluate_roll_status(total_roll: int, dc: int) -> Tuple[str, str]:
        target_dc = dc if dc > 0 else 12
        success = total_roll >= target_dc
        return ("SUCCESS" if success else "FAILURE"), f"DC {target_dc}"

    @staticmethod
    def _clean_name(value: str) -> str:
        text = re.sub(r'[*_`>"]', '', str(value or '')).strip()
        text = re.sub(r"\s+", " ", text)
        return text.strip(" .:-")
