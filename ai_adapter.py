import json
from config import config
from langchain.prompts import ChatPromptTemplate
from logger import setup_logger
from utils import history_as_messages, combine_documents, load_knowledge
from prompts import (
    expert_system_prompt,
    bok_system_prompt,
    response_system_prompt,
    limits_system_prompt,
    translator_system_prompt,
    condenser_system_prompt,
)
from models import chat_llm, condenser_llm

logger = setup_logger(__name__)

braek = 10


async def invoke(message):
    try:
        return query_chain(message)
    except Exception as inst:
        logger.exception(inst)
        return {
            "answer": "Alkemio's VirtualContributor service is currently unavailable.",
            "original_answer": "Alkemio's VirtualContributor service is currently unavailable.",
            "sources": [],
        }


# how do we handle languages? not all spaces are in Dutch obviously
# translating the question to the data _base language_ should be a separate call
# so the translation could be used for embeddings retrieval
async def query_chain(message):

    # use the last N message from the history except the last one
    # as it is the question we are answering now
    history = message["history"][(config["history_length"] + 1) * -1 : -1]
    question = message["question"]

    # if we have history try to add context from it into the last question
    # - who is Maxima?
    # - Maxima is the Queen of The Netherlands
    # - born? =======> rephrased to: tell me about the birth of Queen Máxima of the Netherlands
    if len(history) > 0:
        logger.info("We have history. Let's rephrase.")
        condenser_messages = [("system", condenser_system_prompt)]
        condenser_promt = ChatPromptTemplate.from_messages(condenser_messages)
        condenser_chain = condenser_promt | condenser_llm

        result = condenser_chain.invoke(
            {"question": question, "chat_history": history_as_messages(history)}
        )
        logger.info(
            f"Original question is: '{question}'; Rephrased question is: '{result.content}"
        )
        question = result.content
    else:
        logger.info("No history to handle, initial interaction")

    knowledge_docs = load_knowledge(question, message["bodyOfKnowledgeID"])

    # TODO bring back the context space usage
    # context_docs = load_context(question, message["contextID"])

    logger.info("Creating expert prompt. Applying system messages...")
    expert_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", expert_system_prompt),
            ("system", bok_system_prompt),
            ("system", response_system_prompt),
            ("system", limits_system_prompt),
        ]
    )
    logger.info("System messages applied.")
    logger.info("Adding history...")
    expert_prompt += history_as_messages(history)
    logger.info("History added.")
    logger.info("Adding last question...")
    expert_prompt.append(("human", "{question}"))
    logger.info("Last question added.")
    expert_chain = expert_prompt | chat_llm

    if knowledge_docs["ids"] and knowledge_docs["metadatas"]:
        logger.info("Invoking expert chain...")
        result = expert_chain.invoke(
            {
                "question": question,
                "knowledge": combine_documents(knowledge_docs),
            }
        )
        json_result = {}
        logger.info(f"Expert chain invoked. Result is `{str(result.content)}`")
        try:
            # try to parse a valid JSON response from the main expert engine
            json_result = json.loads(str(result.content))
            logger.info("Engine chain returned valid JSON.")
        except:
            # not an actual error; behaviour is semi-expected
            logger.info(
                "Engine chain returned invalid JSON. Falling back to default result schema."
            )
            json_result = {
                "answer": result.content,
                "original_answer": result.content,
                "source_scores": {},
            }

        # if we have the human language
        if (
            "human_language" in json_result
            and "answer_language" in json_result
            and json_result["human_language"] != json_result["answer_language"]
        ):
            target_lang = json_result["human_language"]
            logger.info(
                f"Creating translsator chain. Human language is {target_lang}; answer language is {json_result['answer_language']}"
            )
            translator_prompt = ChatPromptTemplate.from_messages(
                [("system", translator_system_prompt), ("human", "{text}")]
            )
            translator_chain = translator_prompt | chat_llm

            translation_result = translator_chain.invoke(
                {
                    "target_language": target_lang,
                    "text": json_result["answer"],
                }
            )
            json_result["original_answer"] = json_result.pop("answer")
            json_result["answer"] = translation_result.content
            logger.info(f"Translation completed. Result is: {json_result['answer']}")
        else:
            logger.info("Translation not needed or impossible.")
            json_result["original_answer"] = json_result["answer"]

        source_scores = json_result.pop("source_scores")
        if len(source_scores) > 0:
            # add score and URI to the sources
            sources = [
                dict(doc)
                # most of this processing should be removed from here
                | {
                    "score": source_scores[str(index)],
                    "uri": doc["source"],
                    "title": "[{}] {}".format(
                        str(doc["type"]).replace("_", " ").lower().capitalize(),
                        doc["title"],
                    ),
                }
                for index, doc in enumerate(knowledge_docs["metadatas"][0])
            ]
            json_result["sources"] = list(
                {doc["source"]: doc for doc in sources}.values()
            )

        return json_result

    return {"answer": "", "original_answer": "", "sources": []}
