import re
import time
from alkemio_virtual_contributor_engine import (
    Input, Response, setup_logger, HistoryItem, MessageSenderRole,
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
    last_msg = state.messages[-1]
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

        # Append current message to history for the graph
        full_history = list(input.history) + [
            HistoryItem(content=input.message, role=MessageSenderRole.HUMAN)
        ]

        logger.info(f"Invoking graph for bok_id={input.body_of_knowledge_id} "
                    f"history_messages={len(full_history)}")
        logger.debug(f"Full conversation history: {history_as_dict(full_history)}")

        graph = prompt_graph.compile(llm=mistral_small, special_nodes={"retrieve": retrieve})
        start_time = time.time()
        result = graph.invoke({
            "messages": history_as_dict(full_history),
            "conversation": history_as_conversation(full_history),
            "bok_id": input.body_of_knowledge_id,
            "description": input.description,
            "display_name": input.display_name,
        })
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

        logger.debug(f"Retrieved knowledge docs: {knowledge_docs}")
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
