"""
AVRAE_PARSER.PY - Az Avrae bot Discord üzeneteinek és beágyazott kártyáinak (Embeds) 
szöveges elemzéséért és mechanikai kiértékeléséért felelős szolgáltatás.
"""

import re
from typing import List, Optional, Tuple


class AvraeParserService:
    """
    Felelős az Avrae bot által küldött komplex Discord Embedek elemzéséért,
    a kockadobások értékének kinyeréséért és a harci állapotok detektálásáért.
    """

    @staticmethod
    def extract_full_text(embeds: List) -> str:
        """
        Összefűzi egy Discord Embed összes szöveges mezőjét (cím, leírás, szerző, mezők),
        hogy egyetlen kereshető stringet kapjunk az elemzéshez.
        """
        if not embeds:
            return ""
            
        embed = embeds[0] if isinstance(embeds, list) else embeds
        title = embed.title or ""
        desc = embed.description or ""
        author_name = embed.author and embed.author.name or ""
        
        full_text = f"{title} \n {desc} \n {author_name}"
        
        if embed.fields:
            for field in embed.fields:
                full_text += f" \n {field.name} \n {field.value}"
                
        return full_text

    @staticmethod
    def is_combat_trigger(text: str) -> bool:
        """Megvizsgálja, hogy a szöveg alapján az Avrae harci kezdeményezést indított-e."""
        keywords = ["initiative", "combat", "kezdeményezés"]
        return any(kw in text.lower() for kw in keywords)

    @staticmethod
    def is_hp_update(text: str) -> bool:
        """Megvizsgálja, hogy a szöveg tartalmaz-e életerő (HP) változásra utaló jeleket."""
        return "hp:" in text.lower() or "❤️" in text

    @staticmethod
    def is_death_event(text: str) -> bool:
        """Megvizsgálja, hogy az Avrae jelzett-e karakter vagy szörnyhalált."""
        return "dead" in text.lower() or "dying" in text.lower()

    @staticmethod
    def extract_total_roll(text: str) -> Optional[int]:
        """
        Regex segítségével megpróbálja kinyerni az Avrae dobásának végeredményét.
        Például: 'Total: 15 = 19' -> 19
        """
        # Megkeressük az utolsó egyenlőségjel után álló számot
        match = re.search(r'=\s*(\d+)', text)
        if match:
            return int(match.group(1))
            
        # Ha nincs egyenlőségjel, kimentjük az összes különálló számot és az utolsót vesszük
        numbers = re.findall(r'\b\d+\b', text)
        if numbers:
            return int(numbers[-1])
            
        return None

    @staticmethod
    def evaluate_roll_status(total_roll: int, dc: int) -> Tuple[str, str]:
        """Összeveti a dobást a célszámmal és visszaadja a szöveges státuszt."""
        target_dc = dc if dc > 0 else 12
        success = total_roll >= target_dc
        return ("SUCCESS" if success else "FAILURE"), f"DC {target_dc}"
