import os
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from langchain_core.prompts import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_openai import AzureChatOpenAI
from config import config, local_path, LOG_LEVEL, max_token_limit


import os
from logger import setup_logger

logger = setup_logger(__name__)

# verbose output for LLMs
if LOG_LEVEL == "DEBUG":
    verbose_models = True
else:
    verbose_models = False

# define internal configuration parameters

chat_system_template = """
You are a friendly and talkative conversational agent, tasked with answering questions based on the context provided below delimited by triple pluses.
Use the following step-by-step instructions to respond to user inputs:

1 - Provide an answer of 250 words or less that is professional, engaging, accurate and exthausive If the answer cannot be found within the context, write 'Hmm, I am not sure'. 
2 - If the question is not is not professional write 'Unfortunately, I cannot answer that question'. 
3 - Only return the answer from step 3, do not show any code or additional information.
5 - Always answer in Dutch.

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


embed_func = embedding_functions.OpenAIEmbeddingFunction(
    api_key=config["openai_api_key"],
    api_base=config["openai_endpoint"],
    api_type="azure",
    api_version=config["openai_api_version"],
    model_name=config["embeddings_deployment_name"],
)


def _combine_documents(docs, document_separator="\n\n"):
    return document_separator.join(docs)


async def query_chain(message):

    logger.info(message)
    logger.info(message["spaceNameID"])

    chroma_client = chromadb.HttpClient(host=config["db_host"], port=config["db_port"])

    collection = chroma_client.get_collection(
        message["spaceNameID"], embedding_function=embed_func
    )

    docs = collection.query(query_texts=[message["question"]], n_results=4)

    logger.info(docs["ids"])

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

    result = review_chain.invoke(
        {
            "question": message["question"],
            "context": _combine_documents(docs["documents"][0]),
        }
    )

    return {"answer": result, "source_documents": docs["metadatas"][0]}
