from config import config
from chromadb.utils.embedding_functions.openai_embedding_function import (
    OpenAIEmbeddingFunction,
)
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from logger import setup_logger
from dotenv import load_dotenv
from langchain_mistralai.chat_models import ChatMistralAI


logger = setup_logger(__name__)

# llm = ChatCompletionsClient(
#     endpoint=config["mistral_endpoint"],
#     credential=AzureKeyCredential(config["mistral_api_key"]),
# )

llm = ChatMistralAI(
    endpoint=config["mistral_endpoint"],
    mistral_api_key=config["mistral_api_key"],
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
    deployment_id=config["embeddings_deployment_name"],
)
