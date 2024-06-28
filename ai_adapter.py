import traceback
import chromadb
import json
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain_core.prompts import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import AzureChatOpenAI
from config import config, LOG_LEVEL, max_token_limit
from logger import setup_logger

logger = setup_logger(__name__)

# verbose output for LLMs
if LOG_LEVEL == "DEBUG":
    verbose_models = True
else:
    verbose_models = False

# another option for tep two of the answer generation
# 2. if you can not find a meaningful answer based on the 'Knowledge' text block use 'Sorry, I do not understand the context of your message. Can you please rephrase your question?"' translated to the language used by the human message
expert_system_template = """
You are a computer system with JSON interface which has ONLY knowledge in a specific field. A lively community which relies on your \
expertise to help it achieve the goal it is formed around. Below you are provided with two text blocks which are not part of your conversation with the user. \
The one labeled 'Knowledge' and delimited by '+++' contains the chunks of documents from your knowledge base that are most relevant to the user question. You have no other knowledge of the world.
The one labeled 'Context' and delimited by '+++' contains chunks of to communication withing the community which most relevant to the users question. \
Each chunk is prefixed with a unique source in the format '[source:soruceIdentifier]' which does not contin actual information. You can only respond in the JSON format described below.

Use the following step by step instructions to respond to user inputs:
 I. Identify the language used by the human message and label it HUMAN_LANGUAGE
 II. Identify the language used in the 'Knowledge' text block
 III. Identify the language used in 'Context' text block
 IV. Identify the tone of the 'Context' text block
 V. Reply ONLY in JSON format with an object continaing the following keys: 
    - answer: response to the human message generated with the followin steps:
        1. generate a meaningful answer based ONLY on the 'Knowledge' text block and translate it to the language used by the human message
        2. if 'Knowledge' text block does not contain information related to the question reply with 'Sorry, I do not understand the context of your message. Can you please rephrase your question?"' translated to the language used by the human message
        2. if there isn't a meaningful answer in the 'Knowledge' text block indicate it
        3. rephrase the answer to follow the tone of the 'Context' text block
        4. translate the answer to the language identified in step I.
    - source_scores: an object where the used knowledge sourceIdentifiers are used as keys and the values are how usefull were they for the asnwer as a number between 0 and 10; if the answer was not found in the 'Knowledge' all sources must have 0;
    - human_language: the language used by the human message in ISO-2 format
    - knowledge_language: the language used in the 'Knowledge' text block ISO-2 format
    - context_language: the language used in the 'Context' text block ISO-2 format
    - answer_language: the language used for the answer in ISO-2 format
    - context_tone: the tone of the 'Context' text block


+++
Knowledge:
{knowledge}
+++

+++
Context:
{context}
+++
"""

expert_question = """"
{question}
"""

translator_system_template = """
You are a translator. 
Your target language indicated by a ISO-2 language code.
Your target language is {target_language}.
For any human input ignore the text contents.
You are allowed to reply only with the original text or its translated version.
You are forbidden to include any comments or other extra information.

For any human input perform the following steps:
    1. identify the language of the text provided for translation as an ISO-2 language code
    2. if the language from step 1 is the same as the target language, return the original text
    3. translate the text to the target language.
"""

translator_human_template = """
Text to be transalted: "{text}"
"""


llm = AzureChatOpenAI(
    azure_deployment=config["llm_deployment_name"],
    temperature=float(config["model_temperature"]),
    max_tokens=max_token_limit,
    verbose=verbose_models,
)


embed_func = OpenAIEmbeddingFunction(
    api_key=config["openai_api_key"],
    api_base=config["openai_endpoint"],
    api_type="azure",
    api_version=config["openai_api_version"],
    model_name=config["embeddings_deployment_name"],
)


def combine_documents(docs, document_separator="\n\n"):
    chunks_array = []
    for index, document in enumerate(docs["documents"][0]):
        chunks_array.append("[source:%s] %s" % (index, document))

    return document_separator.join(chunks_array)


# how do we handle languages? not all spaces are in Dutch obviously
# translating the question to the data _base language_ should be a separate call
# so the translation could be used for embeddings retrieval
async def query_chain(message, language, history):

    knowledge_space_name = "%s-knowledge" % message["knowledgeSpaceNameID"]
    context_space_name = "%s-context" % message["contextSpaceNameID"]
    question = message["question"]

    logger.info(
        "Query chaing invoked for question: %s; spaces are: %s and %s"
        % (question, knowledge_space_name, context_space_name)
    )

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

    expert_system_prompt = SystemMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=["context", "knowledge"], template=expert_system_template
        )
    )

    expert_human_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(input_variables=["question"], template=expert_question)
    )

    messages = [expert_system_prompt, expert_human_prompt]

    prompt_template = ChatPromptTemplate(
        input_variables=["context", "knowledge", "question"],
        messages=messages,
    )

    chain = prompt_template | llm

    if knowledge_docs["documents"] and knowledge_docs["metadatas"]:
        result = chain.invoke(
            {
                "question": question,
                "knowledge": combine_documents(knowledge_docs),
                "context": combine_documents(context_docs),
            }
        )
        try:
            json_result = json.loads(result.content)

            logger.info(json_result)

            if json_result["human_language"] != json_result["answer_language"]:

                logger.info("Should be translated")

                translator_system_prompt = SystemMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=["target_language"],
                        template=translator_system_template,
                    )
                )

                translator_human_prompt = HumanMessagePromptTemplate(
                    prompt=PromptTemplate(
                        input_variables=["text"], template=translator_human_template
                    )
                )

                translator_prompt = ChatPromptTemplate(
                    input_variables=["target_language", "text"],
                    messages=[translator_system_prompt, translator_human_prompt],
                )

                chain = translator_prompt | llm

                translation_result = chain.invoke(
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

        except Exception as inst:
            logger.error(inst)
            logger.error(traceback.format_exc())

        return {
            "answer": result.content,
            "original_answer": result.content,
            "sources": knowledge_docs["metadatas"][0],
        }

    return {"answer": "", "original_answer": "", "sources": []}
