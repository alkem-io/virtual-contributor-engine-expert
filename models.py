from config import config
from chromadb.utils.embedding_functions.openai_embedding_function import (
    OpenAIEmbeddingFunction,
)
from logger import setup_logger
from langchain_mistralai.chat_models import ChatMistralAI


logger = setup_logger(__name__)
llm = ChatMistralAI(
    endpoint=config["mistral_endpoint"],
    mistral_api_key=config["mistral_api_key"],
)

embed_func = OpenAIEmbeddingFunction(
    api_key=config["openai_api_key"],
    api_base=config["openai_endpoint"],
    api_type="azure",
    api_version=config["openai_api_version"],
    deployment_id=config["embeddings_deployment_name"],
)
