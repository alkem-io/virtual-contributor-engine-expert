"""Node class for representing execution nodes in the prompt graph."""

from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel, Field, ConfigDict
from .json_graph_parser import parse_json_graph


class Node(BaseModel):
    """Represents a node in the prompt graph that processes state and produces output.

    Each node has:
    - A name for identification
    - Input variables it expects from the state
    - A prompt template for LLM interaction
    - An output schema that defines the structure of its output
    - An output model (Pydantic) built from the output schema

    Attributes:
        name: Unique identifier for this node
        input_variables: List of state variable names this node requires
        prompt: The prompt template string (may contain {variable} placeholders)
        output_schema: JSON schema defining the structure of this node's output
        output_model: Pydantic model class for validating and structuring output
    """

    name: str = Field(..., description="Unique name for this node")
    input_variables: List[str] = Field(
        default_factory=list,
        description="List of input variable names from state"
    )
    prompt: str = Field("", description="Prompt template for this node")
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        alias="output",
        description="JSON schema for the node's output structure"
    )
    output_model: Optional[Type[BaseModel]] = Field(
        None,
        exclude=True,  # Don't include in serialization
        description="Pydantic model built from output_schema"
    )

    model_config = ConfigDict(
        validate_by_name=True,
        arbitrary_types_allowed=True,
    )

    def __init__(self, **data: Any):
        """Initialize the Node and build its output model from the schema.

        This automatically creates a Pydantic model from the output_schema
        when the node is instantiated.
        """
        super().__init__(**data)

        # Build the output model from the schema if not already provided
        if self.output_schema and not self.output_model:
            self.output_model = self._build_output_model()

    def _build_output_model(self) -> Type[BaseModel]:
        """Build a Pydantic model from the output schema.

        Returns:
            A Pydantic BaseModel class that validates node output
        """
        # The output schema should already be in the right format
        # Ensure it has a title for model naming
        schema = dict(self.output_schema)
        schema.setdefault("title", f"{self.name.title().replace('_', '')}Output")

        # Use the existing transformation and model building logic
        output_model = parse_json_graph(schema)
        return output_model

    def validate_output(self, output_data: Dict[str, Any]) -> BaseModel:
        """Validate output data against this node's output model.

        Args:
            output_data: Dictionary of output data from node execution

        Returns:
            Validated Pydantic model instance

        Raises:
            ValidationError: If output_data doesn't match the schema
        """
        if not self.output_model:
            raise ValueError(f"No output model defined for node '{self.name}'")

        return self.output_model(**output_data)

    def format_prompt(self, state: BaseModel) -> str:
        """Format the prompt template with values from state.

        Args:
            state: The current graph state containing input variables

        Returns:
            Formatted prompt string with variables replaced

        Raises:
            KeyError: If required input variables are missing from state
        """
        # Extract values for input variables from state
        values: Dict[str, Any] = {}
        for var in self.input_variables:
            if hasattr(state, var):
                values[var] = getattr(state, var)
            else:
                raise KeyError(
                    f"Required input variable '{var}' not found in state "
                    f"for node '{self.name}'"
                )

        # Format the prompt template
        try:
            formatted_prompt = self.prompt.format(**values)
            return formatted_prompt
        except KeyError as e:
            raise KeyError(
                f"Prompt template for node '{self.name}' requires variable "
                f"{e} which was not provided"
            )

    def execute(
        self,
        state: BaseModel,
        llm_function: Optional[Callable[[str], Dict[str, Any]]] = None
    ) -> BaseModel:
        """Execute this node with the given state.

        Args:
            state: Current graph state
            llm_function: Optional function to call LLM with formatted prompt
                         Should return a dict matching the output schema

        Returns:
            Validated output model instance

        Note:
            This is a basic implementation. Subclasses or external logic
            should provide actual LLM integration via llm_function.
        """
        # Format the prompt with state values
        formatted_prompt = self.format_prompt(state)

        # If no LLM function provided, raise an error
        if llm_function is None:
            raise NotImplementedError(
                f"Node '{self.name}' requires an llm_function to execute. "
                "Provide a callable that takes a prompt and returns output dict."
            )

        # Call the LLM function
        output_data = llm_function(formatted_prompt)

        # Validate and return the output
        return self.validate_output(output_data)

    def __repr__(self) -> str:
        inputs = ", ".join(self.input_variables) if self.input_variables else "none"
        return f"Node(name='{self.name}', inputs=[{inputs}])"
