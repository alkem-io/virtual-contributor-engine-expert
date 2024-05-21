import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from langchain_core.prompts import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_openai import AzureChatOpenAI
from numpy import source
from config import config, local_path, LOG_LEVEL, max_token_limit


import os
from logger import setup_logger

logger = setup_logger(__name__)

# verbose output for LLMs
if LOG_LEVEL == "DEBUG":
    verbose_models = True
else:
    verbose_models = False

chat_system_template = """
You are a friendly and talkative conversational agent, tasked with answering questions based on the context provided below delimited by triple pluses.
Use the following step-by-step instructions to respond to user inputs:
1 - If the question is in a different language than Dutch, translate the question to Dutch before answering.
2 - The text provided in the context delimited by triple pluses is retrieved from the Alkemio platform and is not part of the conversation with the user.
3 - Provide an answer of 250 words or less that is professional, engaging, accurate and exthausive, based on the context delimited by triple pluses. \
If the answer cannot be found within the context, write 'Hmm, I am not sure'. 
4 - If the question is not specifically about Alkemio or if the question is not professional write 'Unfortunately, I cannot answer that question'. 
5 - Only return the answer from step 3, do not show any code or additional information.
6 - Answer in Dutch.
+++
{context}
+++
"""

condense_question_template = """"
{question}
"""


condense_question_prompt = PromptTemplate.from_template(condense_question_template)

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", chat_system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)


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


def _combine_documents(docs, document_separator="\n\n"):
    return document_separator.join(docs)


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
    collection = chroma_client.get_collection(
        knowledge_space_name, embedding_function=embed_func
    )

    docs = collection.query(
        query_texts=[question], include=["documents", "metadatas"], n_results=4
    )

    logger.info(docs["metadatas"])
    logger.info("Documents with ids [%s] selected" % ",".join(list(docs["ids"][0])))

    review_system_prompt = SystemMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=["context"], template=chat_system_template
        )
    )

    review_human_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=["question"], template=condense_question_template
        )
    )

    messages = [review_system_prompt, review_human_prompt]

    review_prompt_template = ChatPromptTemplate(
        input_variables=["context", "question"],
        messages=messages,
    )

    review_chain = review_prompt_template | llm

    if docs["documents"] and docs["metadatas"]:
        result = review_chain.invoke(
            {
                "question": question,
                "context": _combine_documents(docs["documents"][0]),
            }
        )
        return {"answer": result, "source_documents": docs["metadatas"][0]}

    return {"answer": "", "source_documents": []}
