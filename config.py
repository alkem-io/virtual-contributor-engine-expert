import os
from dotenv import load_dotenv
load_dotenv()

config = {
    "llm_deployment_name": os.getenv('LLM_DEPLOYMENT_NAME'),
    "embeddings_deployment_name": os.getenv('EMBEDDINGS_DEPLOYMENT_NAME'),
    "openai_api_version": os.getenv('OPENAI_API_VERSION'),
    "rabbitmq_host": os.getenv('RABBITMQ_HOST'),
    "rabbitmq_user": os.getenv('RABBITMQ_USER'),
    "rabbitmq_password": os.getenv('RABBITMQ_PASSWORD'),
    "rabbitmq_queue": os.getenv('RABBITMQ_QUEUE'),
    "source_website": os.getenv('AI_SOURCE_WEBSITE'),
    "local_path": os.getenv('AI_LOCAL_PATH')
}

local_path = config['local_path']
vectordb_path = local_path + os.sep + 'vectordb'

chunk_size = 3000
# token limit for for the completion of the chat model, this does not include the overall context length
max_token_limit = 2000

LOG_LEVEL = os.getenv('LOG_LEVEL') # Possible values: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
assert LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']