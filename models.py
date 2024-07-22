from langchain_openai import AzureChatOpenAI, AzureOpenAI
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from config import config, LOG_LEVEL, max_token_limit
from langchain_mistralai.chat_models import ChatMistralAI


# verbose output for LLMs
if LOG_LEVEL == "DEBUG":
    verbose_models = True
else:
    verbose_models = False


chat_llm = ChatMistralAI(
    endpoint=config["mistral_endpoint"],
    api_key=config["mistral_api_key"],
    # azure_deployment=config["llm_deployment_name"],
    # temperature=float(config["model_temperature"]),
    # max_tokens=max_token_limit,
    # verbose=verbose_models,
)

condenser_llm = ChatMistralAI(
    endpoint=config["mistral_endpoint"],
    api_key=config["mistral_api_key"],
    # azure_deployment=config["llm_deployment_name"],
    # temperature=0,
    # max_tokens=max_token_limit,
    # verbose=verbose_models,
)

embed_func = OpenAIEmbeddingFunction(
    api_key=config["openai_api_key"],
    api_base=config["openai_endpoint"],
    api_type="azure",
    api_version=config["openai_api_version"],
    model_name=config["embeddings_deployment_name"],
)
