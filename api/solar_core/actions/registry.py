"""Registry for actions: register, list, retrieve."""
from solar_core.actions.base import BaseAction
from solar_core.actions.builtin import ExtractAction, SummarizeAction, TranslateAction
from solar_core.core.exceptions import ActionError


class ActionRegistry:
    """Singleton-style registry of available actions."""

    _instance: "ActionRegistry | None" = None

    def __new__(cls) -> "ActionRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions = {}
            cls._instance._register_builtins()
        return cls._instance

    def _register_builtins(self) -> None:
        for action_cls in (SummarizeAction, ExtractAction, TranslateAction):
            self.register(action_cls())

    def register(self, action: BaseAction) -> None:
        """Register an action instance."""
        self._actions[action.name] = action

    def get(self, name: str) -> BaseAction:
        """Get an action by name."""
        if name not in self._actions:
            raise ActionError(
                f"Unknown action: {name}",
                {"available": list(self._actions.keys())},
            )
        return self._actions[name]

    def list_actions(self) -> list[dict[str, str]]:
        """List all registered actions with name + description."""
        return [
            {"name": a.name, "description": a.description}
            for a in self._actions.values()
        ]


def get_registry() -> ActionRegistry:
    """Get the global action registry."""
    return ActionRegistry()
