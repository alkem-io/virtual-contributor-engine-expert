"""Example usage of the prompt-graph module.

This demonstrates how to:
1. Load a graph from JSON
2. Access nodes and their properties
3. Validate the graph structure
4. Execute the graph (with mock LLM function)
"""

from pathlib import Path
from typing import Any, Dict
from graph import Graph


def mock_llm_function(prompt: str) -> Dict[str, Any]:
    """Mock LLM function for testing.

    In production, this would call an actual LLM API.
    """
    # Simple mock that returns dummy data based on which node is calling
    if "conversation analyser" in prompt.lower():
        return {
            "rephrased_question": "What is your question?",
            "context_answer": None,
            "context_question": "Could you provide more details?"
        }
    elif "retrieve" in prompt.lower():
        return {
            "knowledge_docs": {"doc1": "Some knowledge"}
        }
    elif "chatbot computer system" in prompt.lower():
        return {
            "knowledge_answer": "Here is my answer based on the knowledge base.",
            "source_scores": {"0": 8, "1": 5},
            "human_language": "en",
            "answer_language": "en",
            "knowledge_language": "en"
        }
    elif "evaluate" in prompt.lower():
        return {
            "final_answer": "This is the final evaluated answer.",
            "original_answer": "Original answer before translation"
        }
    else:
        return {}


def main():
    # Load graph from JSON file
    graph_path = Path(__file__).parent / "prompt.graph.expert.json"
    print(f"Loading graph from: {graph_path}")

    graph = Graph.from_json(graph_path)

    print(f"\n{graph}")
    print("\n" + graph.visualize())

    # Validate graph
    print("\n" + "=" * 50)
    print("Validating graph...")
    errors = graph.validate_graph()
    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Graph is valid!")

    # Inspect individual nodes
    print("\n" + "=" * 50)
    print("Node Details:")
    print("=" * 50)

    for node_name, node in graph.nodes.items():
        print(f"\nNode: {node.name}")
        print(f"  Input variables: {node.input_variables}")
        print(f"  Output model: {node.output_model.__name__ if node.output_model else 'None'}")

        if node.output_model:
            print(f"  Output fields: {list(node.output_model.model_fields.keys())}")

    # Example: Execute the graph (commented out by default)
    # Uncomment to test execution with mock LLM
    """
    print("\n" + "=" * 50)
    print("Executing graph...")
    print("=" * 50)

    initial_state = {
        "messages": [
            {"type": "human", "content": "What is the meaning of life?"}
        ],
        "bok_id": "knowledge_base_1"
    }

    try:
        final_state = graph.execute(
            initial_state=initial_state,
            llm_function=mock_llm_function
        )
        print("\n✓ Graph execution completed!")
        print(f"Final answer: {final_state.final_answer}")
    except Exception as e:
        print(f"\n✗ Graph execution failed: {e}")
    """


if __name__ == "__main__":
    main()
