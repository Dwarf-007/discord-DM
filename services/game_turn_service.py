"""
SERVICES/GAME_TURN_SERVICE.PY
Main synchronous orchestration pipeline for one AI DM turn.

Now includes deterministic rest, visibility-aware Donjon movement/look/search,
and legacy room-to-room movement pre-processing.
"""

from __future__ import annotations

from typing import Optional

from core.turn_output import TurnOutput
from llm.llm_response_parser import LLMResponseParser
from services.context_service import ContextService
from services.prompt_builder import PromptBuilder
from services.story_engine import StoryEngine

try:
    from services.runtime_visibility_movement_adapter import RuntimeVisibilityMovementAdapter
    from services.runtime_visibility_turn_output import make_turn_output
except Exception:  # pragma: no cover - optional integration layer
    RuntimeVisibilityMovementAdapter = None  # type: ignore
    make_turn_output = None  # type: ignore


class GameTurnService:
    def __init__(
        self,
        channel_repo,
        party_repo,
        context_service: ContextService,
        prompt_builder: PromptBuilder,
        llm_adapter,
        story_engine: StoryEngine,
        parser: Optional[LLMResponseParser] = None,
        movement_service=None,
        rest_service=None,
        replace_player_placeholder: bool = True,
        campaign_repo=None,
        project_root: str = ".",
        visibility_movement_adapter=None,
    ) -> None:
        self.channel_repo = channel_repo
        self.party_repo = party_repo
        self.context_service = context_service
        self.prompt_builder = prompt_builder
        self.llm_adapter = llm_adapter
        self.story_engine = story_engine
        self.parser = parser or LLMResponseParser()
        self.movement_service = movement_service
        self.rest_service = rest_service
        self.replace_player_placeholder = replace_player_placeholder
        self.campaign_repo = campaign_repo
        self.project_root = project_root

        if visibility_movement_adapter is not None:
            self.visibility_movement_adapter = visibility_movement_adapter
        elif RuntimeVisibilityMovementAdapter is not None:
            self.visibility_movement_adapter = RuntimeVisibilityMovementAdapter(
                campaign_repo=campaign_repo,
                project_root=project_root,
            )
        else:
            self.visibility_movement_adapter = None

    def process(self, channel_id: str, player_id: str, text: str) -> TurnOutput:
        channel_id = str(channel_id)
        player_id = str(player_id)
        text = str(text or "").strip()

        if not text:
            return TurnOutput(public_narrative="Nem hallatszik érthető akció. Kérlek írd le, mit teszel.")

        self._pre_turn_state_update(channel_id, player_id, text)

        # 1) Visibility-aware Donjon runtime pre-processing.
        # This intentionally runs before legacy rest/movement and before LLM.
        # It only handles clear look/move/search-secret intents when a processed
        # Donjon bundle exists for the active campaign. Otherwise it returns None
        # and the legacy flow continues unchanged.
        visibility_output = self._try_handle_visibility_runtime(channel_id, player_id, text)
        if visibility_output is not None:
            return self._finalize_output(visibility_output, player_id)

        # 2) Deterministic rest handling.
        if self.rest_service:
            rest_output = self.rest_service.try_handle_rest(channel_id, player_id, text)
            if rest_output is not None:
                return self._finalize_output(rest_output, player_id)

        # 3) Legacy room-to-room movement fallback.
        if self.movement_service:
            movement_output = self.movement_service.try_handle_movement(channel_id, text, player_id=player_id)
            if movement_output is not None:
                return self._finalize_output(movement_output, player_id)

        # 4) LLM/RAG/story pipeline.
        context = self.context_service.get_context(channel_id=channel_id, player_id=player_id, player_message=text)
        prompt = self.prompt_builder.build(context, text)
        raw_response = self.llm_adapter.generate(prompt)
        llm_response = self.parser.parse(raw_response)

        active_players = self.party_repo.get_party_members(channel_id) or [player_id]
        output = self.story_engine.apply(channel_id=channel_id, player_id=player_id, response=llm_response, active_players=active_players)
        return self._finalize_output(output, player_id)

    def _try_handle_visibility_runtime(self, channel_id: str, player_id: str, text: str) -> Optional[TurnOutput]:
        if not self.visibility_movement_adapter:
            return None

        campaign_id = self._active_campaign_id(channel_id)
        if not campaign_id:
            return None

        result = self.visibility_movement_adapter.try_handle(
            channel_id=channel_id,
            player_id=player_id,
            campaign_id=campaign_id,
            text=text,
        )
        if not result or not result.get("handled"):
            return None

        public_text = result.get("text") or "A helyzet változatlan."
        debug = {"visibility_result": result.get("raw"), "campaign_id": campaign_id}

        if make_turn_output is not None:
            return make_turn_output(public_text, debug=debug)

        return TurnOutput(public_narrative=public_text)

    def _active_campaign_id(self, channel_id: str) -> Optional[str]:
        """Best-effort active campaign lookup from ChannelRepository state.

        Supports the common repository variants used across the refactors:
        - get_state(channel_id) -> dict
        - get_channel_state(channel_id) -> dict
        - load_state(channel_id) -> dict
        Returns 'default' only when the state explicitly lacks campaign_id,
        so non-campaign/freeplay channels can continue through the legacy flow.
        """
        state = None
        for method_name in ("get_state", "get_channel_state", "load_state"):
            method = getattr(self.channel_repo, method_name, None)
            if not method:
                continue
            try:
                state = method(channel_id)
                break
            except Exception:
                continue

        if isinstance(state, dict):
            campaign_id = state.get("campaign_id") or state.get("campaign")
            mode = str(state.get("mode") or "campaign").lower()
            if campaign_id:
                return str(campaign_id)
            if mode == "campaign":
                return "default"
            return None

        return "default"

    def _pre_turn_state_update(self, channel_id: str, player_id: str, text: str) -> None:
        self.party_repo.add_player(channel_id, player_id)
        self.channel_repo.add_player(channel_id, player_id)
        self.channel_repo.append_context_message(channel_id, player_id, text, limit=10)

    def _finalize_output(self, output: TurnOutput, player_id: str) -> TurnOutput:
        if self.replace_player_placeholder:
            output.avrae_commands = [self._replace_player_placeholder(command, player_id) for command in output.avrae_commands]
        if not output.public_narrative:
            output.public_narrative = "A jelenet feszült csendben folytatódik. Mit tesztek?"
        return output

    @staticmethod
    def _replace_player_placeholder(command: str, player_id: str) -> str:
        return str(command).replace("PLAYER", f"<@{player_id}>")
