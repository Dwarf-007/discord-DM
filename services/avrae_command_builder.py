
"""
AVRAE_COMMAND_BUILDER.PY - Converts resolved encounters into Avrae commands.

This module contains formatting logic only.
"""

from typing import List

from core.encounter_models import EncounterResult


class AvraeCommandBuilder:
    """
    Converts a resolved encounter into an ordered list of Avrae commands.
    """

    @staticmethod
    def build_init_commands(encounter: EncounterResult) -> List[str]:
        """
        Builds a deterministic Avrae init sequence.

        Args:
            encounter: Structured encounter result.

        Returns:
            Ordered list of commands to send to Discord.
        """
        commands: List[str] = ["!init begin"]

        for unit in encounter.units:
            commands.append(f"!init add {unit.monster_name} {unit.count}")

        return commands
