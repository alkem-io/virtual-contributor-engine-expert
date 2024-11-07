import re
import json
from alkemio_virtual_contributor_engine.events.input import Input
from alkemio_virtual_contributor_engine.events.result import Response
from config import config
from logger import setup_logger
from utils import (
    clear_tags,
    history_as_text,
    combine_documents,
    load_knowledge,
)
from prompts import (
    expert_system_prompt,
    description_system_prompt,
    bok_system_prompt,
    response_system_prompt,
    limits_system_prompt,
    translator_system_prompt,
    condenser_system_prompt,
)
from models import invoke_model
from azure.ai.inference.models import SystemMessage, UserMessage


logger = setup_logger(__name__)


async def invoke(input: Input) -> Response:
    try:
        # important to await the result before returning
        return await query_chain(input)
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


# how do we handle languages? not all spaces are in Dutch obviously
# translating the message to the data _base language_ should be a separate call
# so the translation could be used for embeddings retrieval
async def query_chain(input: Input):

    # use the last N message from the history except the last one
    # as it is the message we are resulting now
    history = input.history[(config["history_length"] + 1) * -1 : -1]
    message = clear_tags(input.message)

    # if we have history try to add context from it into the last message
    # - who is Maxima?
    # - Maxima is the Queen of The Netherlands
    # - born? =======> rephrased to: tell me about the birth of Queen Máxima of the Netherlands
    if len(history) > 0:
        logger.info(f"We have history. Let's rephrase. Length is: {len(history)}.")
        messages = [
            SystemMessage(
                content=condenser_system_prompt.format(
                    chat_history=history_as_text(history), message=message
                )
            )
        ]
        result = invoke_model(messages)
        logger.info(
            f"Original message is: '{message}'; Rephrased message is: '{result}'"
        )
        message = result
    else:
        logger.info("No history to handle, initial interaction")

    knowledge_docs = load_knowledge(message, input.bok_id)

    # TODO bring back the context space usage
    # context_docs = load_context(message, message["contextID"])

    logger.info("Creating expert prompt. Applying system messages...")
    messages: list[SystemMessage | UserMessage] = [
        SystemMessage(content=expert_system_prompt.format(vc_name=input.display_name)),
        SystemMessage(
            content=bok_system_prompt.format(
                knowledge=combine_documents(knowledge_docs)
            )
        ),
        SystemMessage(content=response_system_prompt),
        SystemMessage(content=limits_system_prompt),
    ]

    if input.description and len(input.description) > 0:
        messages.append(SystemMessage(content=description_system_prompt))

    logger.info("System messages applied.")
    logger.info("Adding history...")
    logger.info("History added.")
    logger.info("Adding last message...")

    messages.append(UserMessage(content=message))

    logger.info("Last message added.")

    if knowledge_docs["ids"] and knowledge_docs["metadatas"]:
        logger.info("Invoking expert chain...")
        result = invoke_model(messages)
        json_result = {}
        logger.info(f"Expert chain invoked. Result is `{result}`")
        try:
            # try to parse a valid JSON response from the main expert engine
            json_result = json.loads(result)
            logger.info("Engine chain returned valid JSON.")
        except:
            # not an actual error; behaviour is semi-expected
            logger.info(
                "Engine chain returned invalid JSON. Falling back to default result schema."
            )
            json_result = {
                "result": result,
                "original_result": result,
                "source_scores": {},
            }

        # if we have the human language
        if (
            "human_language" in json_result
            and "result_language" in json_result
            and json_result["human_language"] != json_result["result_language"]
        ):
            target_lang = json_result["human_language"]
            logger.info(
                f"Creating translsator chain. Human language is {target_lang}; result language is {json_result['result_language']}"
            )
            messages = [
                SystemMessage(
                    content=translator_system_prompt.format(target_language=target_lang)
                ),
                UserMessage(content=json_result["result"]),
            ]
            translated = invoke_model(messages)

            json_result["original_result"] = json_result.pop("result")
            json_result["result"] = translated
            logger.info(f"Translation completed. Result is: {json_result['result']}")
        else:
            logger.info("Translation not needed or impossible.")
            json_result["original_result"] = json_result["result"]

        source_scores = {}
        for source_id, score in json_result.pop("source_scores").items():
            # occasionally the source score keys are returned as 'source:0' and not '0'
            # the processing below will extract the index in both cases
            match = re.search(r"\d+", source_id)
            if match:
                source_id = match.group(0)
            source_scores[source_id] = score

        if len(source_scores) > 0:
            # add score and URI to the sources
            sources = []

            for index, doc in enumerate(knowledge_docs["metadatas"][0]):
                if str(index) in source_scores and source_scores[str(index)] > 0:
                    sources.append(
                        dict(doc)
                        | {
                            "score": source_scores[str(index)],
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

    return Response({"result": "", "original_result": "", "sources": []})
