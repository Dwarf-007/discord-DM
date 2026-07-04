
"""
Central prompt templates for structured Gemini output.
"""

CANONICAL_RESPONSE_CONTRACT = """
KÖTELEZÕ KIMENETI SZABÁLY:
A válaszod KIZÁRÓLAG egyetlen tiszta JSON objektum lehet.
NE használj markdown kódblokkot.
NE írj magyarázatot a JSON elé vagy mögé.
NE használj külön tageket, mint [XP_REWARD], [INVENTORY_UPDATE], [SECRET_TO].

A JSON séma pontosan ez:

{
  "narrative": "A játékosoknak szánt végsõ, tiszta narráció magyarul.",
  "required_check": "Perception | Investigation | Stealth | None",
  "dc": 0,
  "next_room_id": null,
  "xp_reward": 0,
  "milestone_reached": false,
  "inventory_update": {
    "gold": 0.0,
    "items": {},
    "ammo": {}
  },
  "avrae_sync_damage": null,
  "secret_messages": [
    {
      "player_id": "123456789",
      "text": "Titkos információ csak neki."
    }
  ],
  "rest_consequence": {
    "rest_type": "SHORT | LONG | NONE",
    "status": "SUCCESS | INTERRUPTED | NONE",
    "ambush_monster": null
  }
}

TOVÁBBI SZABÁLYOK:
- Ha nincs releváns adat, használj alapértelmezett értéket.
- A "narrative" legyen játékosoknak küldhetõ tiszta szöveg.
- A "secret_messages" NEM kerülhet be a narrative mezõbe.
- A "next_room_id" csak akkor legyen kitöltve, ha a mozgás érvényes.
- A "dc" legyen 0, ha nincs dobáskérés.
- A "required_check" legyen "None", ha nincs szükséges dobás.
"""
