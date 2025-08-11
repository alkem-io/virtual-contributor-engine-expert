from alkemio_virtual_contributor_engine.events.input import Input
from alkemio_virtual_contributor_engine.events.response import Response
from langchain_core.messages import AIMessage, HumanMessage
from alkemio_virtual_contributor_engine.events.input import (
    HistoryItem,
    MessageSenderRole,
)
from logger import setup_logger
from utils import (
    clear_tags,
)
from graph import graph


logger = setup_logger(__name__)

def entry_as_langchain_message(entry):
    if entry.role == MessageSenderRole.HUMAN:
        return HumanMessage(content=clear_tags(entry.content))
    return AIMessage(content=clear_tags(entry.content))

def history_as_langchain_messages(history: list[HistoryItem]):
    return list(map(entry_as_langchain_message, history))


async def invoke(input: Input) -> Response:
    try:
        result = graph.invoke({
            "messages": history_as_langchain_messages(input.history),
            "prompt": input.prompt,
            "bok_id": input.bok_id,
            "description": input.description,
            "display_name": input.display_name,
        })
        json_result = {
            "result": result['final_answer'],
            "original_result": result['final_answer'],
            "human_language": "en",
            "result_language": "en",
            "knowledge_language": "en",
            "source_scores": {},
        }
        knowledge_docs = result.get("knowledge_docs", {})
        source_scores = result.get("source_scores", {})
        sources = []
        if len(source_scores) > 0:
            # add score and URI to the sources
            for index, doc in enumerate(knowledge_docs["metadatas"][0]):
                if index in source_scores and source_scores[index] > 0:
                    sources.append(
                        dict(doc) | {
                            "score": source_scores[index],
                            "uri": doc["source"],
                            "title": "[{}] {}".format(
                                str(doc["type"]).replace("_", " ").lower().capitalize(),
                                doc["title"],
                            ),
                        }
                    )
            json_result["sources"] = list(
                {doc["source"]: doc for doc in sources}.values()
            )

        return Response(json_result)

    except Exception as inst:
        logger.exception(inst)
        result = f"{input.display_name} - the Alkemio's VirtualContributor is currently unavailable."

        return Response(
            {
                "result": result,
                "original_result": result,
                "sources": [],
            }
        )
