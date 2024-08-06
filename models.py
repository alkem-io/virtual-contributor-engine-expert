from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from config import config, LOG_LEVEL
from langchain_mistralai.chat_models import ChatMistralAI


# verbose output for LLMs
if LOG_LEVEL == "DEBUG":
    verbose_models = True
else:
    verbose_models = False


chat_llm = ChatMistralAI(
    endpoint=config["mistral_endpoint"],
    api_key=config["mistral_api_key"],
)

condenser_llm = ChatMistralAI(
    endpoint=config["mistral_endpoint"],
    api_key=config["mistral_api_key"],
)

embed_func = OpenAIEmbeddingFunction(
    api_key=config["openai_api_key"],
    api_base=config["openai_endpoint"],
    api_type="azure",
    api_version=config["openai_api_version"],
    model_name=config["embeddings_deployment_name"],
)
