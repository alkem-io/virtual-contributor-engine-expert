import traceback
import chromadb
import json
from config import config
from langchain.prompts import ChatPromptTemplate
from logger import setup_logger
from utils import history_as_messages, combine_documents
from prompts import (
    expert_system_prompt,
    bok_system_prompt,
    response_system_prompt,
    translator_system_prompt,
    condenser_system_prompt,
)
from models import chat_llm, condenser_llm, embed_func

logger = setup_logger(__name__)


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
            "Original question is: '%s'; Rephrased question is: '%s"
            % (question, result.content)
        )
        question = result.content

    knowledge_space_name = "%s-knowledge" % message["bodyOfKnowledgeID"]
    context_space_name = "%s-context" % message["contextID"]

    logger.info(
        "Query chaing invoked for question: %s; spaces are: %s and %s"
        % (question, knowledge_space_name, context_space_name)
    )

    # try to rework those as retreivers
    chroma_client = chromadb.HttpClient(host=config["db_host"], port=config["db_port"])
    knowledge_collection = chroma_client.get_collection(
        knowledge_space_name, embedding_function=embed_func
    )
    context_collection = chroma_client.get_collection(
        context_space_name, embedding_function=embed_func
    )
    knowledge_docs = knowledge_collection.query(
        query_texts=[question], include=["documents", "metadatas"], n_results=4
    )
    context_docs = context_collection.query(
        query_texts=[question], include=["documents", "metadatas"], n_results=4
    )

    # logger.info(knowledge_docs["metadatas"])
    logger.info(
        "Knowledge documents with ids [%s] selected"
        % ",".join(list(knowledge_docs["ids"][0]))
    )
    logger.info(
        "Context documents with ids [%s] selected"
        % ",".join(list(context_docs["ids"][0]))
    )

    expert_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", expert_system_prompt),
            ("system", bok_system_prompt),
            ("system", response_system_prompt),
        ]
    )
    expert_prompt += history_as_messages(history)
    expert_prompt.append(("human", "{question}"))

    expert_chain = expert_prompt | chat_llm

    if knowledge_docs["documents"] and knowledge_docs["metadatas"]:

        result = expert_chain.invoke(
            {
                "question": question,
                "knowledge": combine_documents(knowledge_docs),
            }
        )
        json_result = {}
        try:
            json_result = json.loads(result.content)
            # try to parse a valid JSON response from the main expert engine
        except Exception as inst:
            # if not log the error and use the result of the engine as plain string
            logger.error(inst)
            logger.error(traceback.format_exc())
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
            translator_prompt = ChatPromptTemplate.from_messages(
                [("system", translator_system_prompt), ("human", "{text}")]
            )

            translator_chain = translator_prompt | chat_llm

            translation_result = translator_chain.invoke(
                {
                    "target_language": json_result["human_language"],
                    "text": json_result["answer"],
                }
            )
            json_result["original_answer"] = json_result.pop("answer")
            json_result["answer"] = translation_result.content
        else:
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
