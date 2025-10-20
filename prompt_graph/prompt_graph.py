"""Graph class for managing and executing prompt graphs."""
from typing import Any, Dict, List, Optional, Type
from typing import Callable
from pydantic import BaseModel, Field, ConfigDict

from .node import Node
from .edge import Edge
from .state import State
from langgraph.graph import StateGraph, START, END
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from utils import load_knowledge, combine_documents
from alkemio_virtual_contributor_engine import mistral_medium as llm, setup_logger

logger = setup_logger(__name__)


def retrieve(state: State):
    logger.info('Retrieving information from the knowledge base.')
    last_message = state.rephrased_question or state.messages[-1].content
    logger.info(f'Retrieving for message: {last_message}')

    knowledge_docs = load_knowledge(last_message, state.bok_id)
    combined_knowledge_docs = combine_documents(knowledge_docs)

    logger.info(f'Retrieved knowledge documents: {combined_knowledge_docs}')
    return {"knowledge_docs": knowledge_docs, "combined_knowledge_docs": combined_knowledge_docs}

class PromptGraph(BaseModel):
    """Represents a complete prompt graph with nodes, edges, and state.

    A Graph orchestrates the execution flow through multiple nodes, managing
    state transitions and coordinating LLM interactions. Special node names
    can be configured via the special_nodes attribute to map node names to
    custom callable functions that bypass the standard prompt/LLM processing.

    Attributes:
        nodes: Dictionary of nodes in the graph, keyed by node name
        edges: List of edges defining the graph structure
        start_node: Name of the starting node (default "START")
        end_node: Name of the ending node (default "END")
        state_model: Pydantic model class for graph state
    special_nodes: Mapping of node names to callable functions for nodes
                   that require custom processing (default: {"retrieve": retrieve})
    """

    nodes: Dict[str, Node] = Field(default_factory=dict, description="Graph nodes by name")
    edges: List[Edge] = Field(default_factory=list, description="Graph edges")
    start_node: str = Field("START", alias="start", description="Starting node name")
    end_node: str = Field("END", alias="end", description="Ending node name")
    special_nodes: Dict[str, Callable] = Field(
        default_factory=lambda: {"retrieve": retrieve},
        description="Mapping of node names to custom callable functions"
    )
    state_model: Optional[Type[BaseModel]] = Field(
        None,
        exclude=True,
        description="Pydantic model for graph state"
    )

    model_config = ConfigDict(
        validate_by_name=True,
        arbitrary_types_allowed=True,
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptGraph":
        """Create a Graph from a dictionary.

        Args:
            data: Dictionary containing graph definition

        Returns:
            Graph instance
        """
        # Parse nodes
        nodes_dict = {}
        for node_data in data.get("nodes", []):
            node = Node(**node_data)
            nodes_dict[node.name] = node

        # Parse edges
        edges = [Edge(**edge_data) for edge_data in data.get("edges", [])]

        # Build state model from schema if provided
        state_model = None
        if "state" in data:
            state_model = State.build_state_model(data["state"])

        # Create graph
        graph = cls(
            nodes=nodes_dict,
            edges=edges,
            start=data.get("start", "START"),
            end=data.get("end", "END"),
        )

        # Set state model directly (after initialization)
        graph.state_model = state_model
        return graph

    def __repr__(self) -> str:
        return (
            f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)}, "
            f"{self.start_node} -> {self.end_node})"
        )

    def validate_graph(self) -> List[str]:
        """Validate the graph structure and return any issues found.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check that all edges reference existing nodes or START/END
        valid_node_names = set(self.nodes.keys()) | {self.start_node, self.end_node}

        for edge in self.edges:
            if edge.from_node not in valid_node_names:
                errors.append(f"Edge references non-existent source node: {edge.from_node}")
            if edge.to_node not in valid_node_names:
                errors.append(f"Edge references non-existent destination node: {edge.to_node}")

        # Check that there's a path from START
        has_start_edge = any(edge.from_node == self.start_node for edge in self.edges)
        if not has_start_edge:
            errors.append(f"No edge from START node ({self.start_node})")

        # Check that there's a path to END
        has_end_edge = any(edge.to_node == self.end_node for edge in self.edges)
        if not has_end_edge:
            errors.append(f"No edge to END node ({self.end_node})")

        return errors

    def visualize(self) -> str:
        """Generate a text-based visualization of the graph.

        Returns:
            String representation of the graph structure
        """
        lines = ["Graph Structure:", "=" * 50]

        # Show nodes
        lines.append(f"\nNodes ({len(self.nodes)}):")
        for name, node in self.nodes.items():
            inputs = ", ".join(node.input_variables) if node.input_variables else "none"
            lines.append(f"  - {name} (inputs: {inputs})")

        # Show edges
        lines.append(f"\nEdges ({len(self.edges)}):")
        for edge in self.edges:
            lines.append(f"  - {edge}")

        # Show start/end
        lines.append(f"\nFlow: {self.start_node} -> ... -> {self.end_node}")

        return "\n".join(lines)

    def compile(self):
        """
        Compile the prompt graph into a LangGraph graph instance.
        Registers all nodes and edges, using self.state_model as the state.
        """

        # Create LangGraph graph with the state model
        compiled_graph = StateGraph(self.state_model)

        # Register nodes
        for node_name, node in self.nodes.items():
            if node_name in self.special_nodes:
                compiled_graph.add_node(node_name, self.special_nodes[node_name])
                continue

            def make_node_fn(node):
                def node_fn(state):
                    # Prepare output parser
                    parser = PydanticOutputParser(pydantic_object=node.output_model)
                    format_instructions = parser.get_format_instructions()

                    # Ensure the prompt contains the required output format instructions.
                    # If missing, append them to the end with two new lines before them.
                    prompt_text = node.prompt
                    required_instr = "Output format instructions: {format_instructions}"
                    if required_instr not in prompt_text:
                        prompt_text = prompt_text + "\n\n" + required_instr

                    # Prepare prompt template using the (possibly modified) prompt text
                    prompt = PromptTemplate(
                        template=prompt_text,
                        input_variables=node.input_variables,
                        partial_variables={"format_instructions": format_instructions}
                    )

                    # Validate all required input variables exist on state
                    missing_vars = [var for var in node.input_variables if not hasattr(state, var)]
                    if missing_vars:
                        raise ValueError(
                            f"Node '{node.name}' is missing required input variables from state: "
                            f"{', '.join(missing_vars)}. Available state attributes: "
                            f"{', '.join(dir(state))}"
                        )

                    # Prepare input for chain from state (all variables validated)
                    input_dict = {var: getattr(state, var) for var in node.input_variables}

                    logger.debug(f"Invoking node '{node.name}' with prompt: {prompt} and inputs: {input_dict}")
                    chain = prompt | llm | parser
                    result = chain.invoke(input_dict)
                    logger.debug(f"Node '{node.name}' produced result: {result}")

                    return result.model_dump()
                return node_fn
            compiled_graph.add_node(node_name, make_node_fn(node))

        # Add edges
        for edge in self.edges:
            if edge.from_node == "START":
                compiled_graph.add_edge(START, edge.to_node)
            elif edge.to_node == "END":
                compiled_graph.add_edge(edge.from_node, END)
            else:
                compiled_graph.add_edge(edge.from_node, edge.to_node)

        return compiled_graph.compile()
