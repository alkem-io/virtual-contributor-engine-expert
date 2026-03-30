import re
import time
from alkemio_virtual_contributor_engine import (
    Input, Response, setup_logger,
    mistral_small, combine_query_results, PromptGraph,
)
from utils import (
    history_as_conversation,
    history_as_dict,
    load_knowledge,
)


logger = setup_logger(__name__)


def retrieve(state):
    """Retrieve knowledge documents from ChromaDB for the current query."""
    last_msg = state.messages[0]
    last_message = state.rephrased_question or (
        last_msg["content"] if isinstance(last_msg, dict) else last_msg.content
    )
    knowledge_docs = load_knowledge(last_message, state.bok_id)
    combined_knowledge_docs = combine_query_results(knowledge_docs)
    return {"knowledge_docs": knowledge_docs, "combined_knowledge_docs": combined_knowledge_docs}


async def invoke(input: Input) -> Response:
    try:
        if not input.prompt_graph:
            raise Exception("promptGraph is required in Input.")

        prompt_graph = PromptGraph.from_dict(input.prompt_graph)

        logger.info(f"Invoking graph for bok_id={input.body_of_knowledge_id} "
                    f"history_messages={len(input.history)}")
        logger.debug(f"Full conversation history: {history_as_dict(input.history)}")

        graph = prompt_graph.compile(llm=mistral_small, special_nodes={"retrieve": retrieve})
        start_time = time.time()
        messages = history_as_dict(input.history)
        input_state = {
            "messages": messages,
            "current_question": messages[0]["content"] if messages else "",
            "conversation": history_as_conversation(input.history),
            "bok_id": input.body_of_knowledge_id,
            "description": input.description,
            "display_name": input.display_name,
        }
        result = {}
        for step in graph.stream(input_state, stream_mode="updates"):
            for node_name, node_output in step.items():
                logger.info(f"Step '{node_name}' completed")
                logger.debug(f"Step '{node_name}' output: {node_output}")
                result.update(node_output)
        duration = time.time() - start_time
        logger.info(f"Graph invocation completed in {duration:.2f}s")

        json_result = {
            "result": result.get("final_answer", ""),
            "original_result": result.get("knowledge_answer", ""),
            "human_language": result.get("human_language", "en"),
            "result_language": result.get("knowledge_language", "en"),
            "knowledge_language": result.get("knowledge_language", "en"),
            "source_scores": {},
        }
        knowledge_docs = result.get("knowledge_docs", {})
        source_scores = result.get("source_scores", {})
        sources = []
        if len(source_scores) > 0:
            # add score and URI to the sources
            for index, doc in enumerate(knowledge_docs["metadatas"][0]):
                str_index = str(index)
                if str_index in source_scores and source_scores[str_index] > 0:
                    sources.append(
                        dict(doc) | {
                            "score": source_scores[str_index],
                            "uri": doc["source"],
                            "title": "[{}] {}".format(
                                re.sub(
                                    r'(?<=[a-z])(?=[A-Z])|_', ' ',
                                    str(doc["type"])
                                ).capitalize(),
                                doc["title"],
                            ),
                        }
                    )
            json_result["sources"] = list(
                {doc["source"]: doc for doc in sources}.values()
            )

        logger.debug(f"Full result: {json_result}")

        return Response(**json_result)

    except Exception as inst:
        logger.exception(inst)
        result = f"{input.display_name} - the Alkemio's VirtualContributor \
        is currently unavailable."

        return Response(
            **{
                "result": result,
                "original_result": result,
                "sources": [],
            }
        )
