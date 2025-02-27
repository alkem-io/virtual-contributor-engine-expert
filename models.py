from chromadb.utils.embedding_functions.openai_embedding_function import (
    OpenAIEmbeddingFunction,
)
from config import config
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from logger import setup_logger

logger = setup_logger(__name__)

llm = ChatCompletionsClient(
    endpoint=config["mistral_endpoint"],
    credential=AzureKeyCredential(config["mistral_api_key"]),
)


def invoke_model(messages):
    result = llm.complete(
        messages=messages,
        temperature=config["model_temperature"],
        top_p=1,
        stream=False,
    )
    logger.debug(result)
    message = str(result["choices"][0]["message"]["content"])
    return message


embed_func = OpenAIEmbeddingFunction(
    api_key=config["openai_api_key"],
    api_base=config["openai_endpoint"],
    api_type="azure",
    api_version=config["openai_api_version"],
    model_name=config["embeddings_deployment_name"],
)
