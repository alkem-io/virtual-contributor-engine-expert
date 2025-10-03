"""Edge class for representing connections between nodes in the prompt graph."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Edge(BaseModel):
    """Represents a directed edge between two nodes in the prompt graph.

    Attributes:
        from_node: The name of the source node (or "START" for graph entry)
        to_node: The name of the destination node (or "END" for graph exit)
        condition: Optional condition for conditional edges
    """

    from_node: str = Field(..., alias="from", description="Source node name")
    to_node: str = Field(..., alias="to", description="Destination node name")
    condition: Optional[str] = Field(None, description="Optional condition for this edge")

    model_config = ConfigDict(
        validate_by_name=True,
    )

    def __repr__(self) -> str:
        if self.condition:
            return f"Edge({self.from_node} -> {self.to_node} [if {self.condition}])"
        return f"Edge({self.from_node} -> {self.to_node})"
