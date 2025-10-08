"""State class for managing the graph execution state."""

from typing import Any, Dict, Type
from pydantic import BaseModel, ConfigDict
from .json_graph_parser import parse_json_graph


class State(BaseModel):
    """Represents the state that flows through the prompt graph during execution.

    The state is dynamically created from the JSON schema definition and holds
    all data that is passed between nodes during graph execution.

    This base class provides methods for state management, but the actual state
    model should be created dynamically using the build_state_model class method.
    """
    model_config = ConfigDict(
        extra="allow",  # Allow additional fields not explicitly defined
        arbitrary_types_allowed=True,
    )

    @classmethod
    def build_state_model(cls, state_schema: Dict[str, Any]) -> Type[BaseModel]:
        """Build a dynamic Pydantic model from a state schema definition.

        This method takes the 'state' portion of the prompt graph JSON and creates
        a Pydantic model class with proper field types and validation.

        Args:
            state_schema: The state schema dictionary from the prompt graph JSON

        Returns:
            A dynamically created Pydantic BaseModel class

        Example:
            >>> state_schema = {
            ...     "title": "MyState",
            ...     "type": "object",
            ...     "properties": {
            ...         "messages": {"type": "array"},
            ...         "bok_id": {"type": "string"}
            ...     },
            ...     "required": ["messages", "bok_id"]
            ... }
            >>> StateModel = State.build_state_model(state_schema)
            >>> state = StateModel(messages=[], bok_id="kb1")
        """

        # Use the existing transformation logic
        state_model = parse_json_graph(state_schema)
        return state_model

    def update(self, **kwargs: Any) -> "State":
        """Update the state with new values.

        Args:
            **kwargs: Key-value pairs to update in the state

        Returns:
            A new State instance with updated values
        """
        # Create a new instance with updated values
        current_data = self.model_dump()
        current_data.update(kwargs)
        return self.__class__(**current_data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state.

        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist

        Returns:
            The value associated with the key, or default if not found
        """
        return getattr(self, key, default)
