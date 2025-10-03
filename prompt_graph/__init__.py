"""Prompt Graph module for building and executing graph-based prompts.

This module provides classes for defining and executing graph-based prompt workflows:

- Graph: Orchestrates the execution of nodes and edges
- Node: Represents a processing step with LLM interaction
- Edge: Defines connections between nodes
- State: Manages data flowing through the graph

Example:
    >>> from pathlib import Path
    >>> graph = Graph.from_json(Path("prompt.graph.expert.json"))
    >>> final_state = graph.execute(initial_state, llm_function)
"""

from .edge import Edge
from .prompt_graph import PromptGraph
from .node import Node
from .state import State
from .json_graph_parser import parse_json_graph

__all__ = ["Edge", "PromptGraph", "Node", "State", "parse_json_graph"]
__version__ = "0.1.0"
