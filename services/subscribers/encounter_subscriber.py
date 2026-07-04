
class EncounterSubscriber:
    """
    Example: reacts to combat events.
    """

    def on_combat_started(self, payload):
        print(
            f"[ENCOUNTER] Combat triggered: "
            f"{payload.get('combat_type')} "
            f"in room {payload.get('room_id')}"
        )
