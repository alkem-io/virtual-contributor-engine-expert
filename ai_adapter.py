from alkemio_virtual_contributor_engine import Input, Response, setup_logger
from utils import (
    history_as_conversation,
    history_as_dict,
)
from prompt_graph import PromptGraph


logger = setup_logger(__name__)

async def invoke(input: Input) -> Response:
    try:
        if not input.prompt_graph:
            raise Exception("promptGraph is required in Input.")

        prompt_graph = PromptGraph.from_dict(input.prompt_graph)

        graph = prompt_graph.compile()
        result = graph.invoke({
            "messages": history_as_dict(input.history),
            "conversation": history_as_conversation(input.history),
            "bok_id": input.body_of_knowledge_id,
            "description": input.description,
            "display_name": input.display_name,
        })

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
                                str(doc["type"]).replace("_", " ").lower().capitalize(),
                                doc["title"],
                            ),
                        }
                    )
            json_result["sources"] = list(
                {doc["source"]: doc for doc in sources}.values()
            )

        return Response(**json_result)

    except Exception as inst:
        logger.exception(inst)
        result = f"{input.display_name} - the Alkemio's VirtualContributor is currently unavailable."

        return Response(
            **{
                "result": result,
                "original_result": result,
                "sources": [],
            }
        )
