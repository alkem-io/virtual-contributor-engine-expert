import os
from dotenv import load_dotenv
load_dotenv()

config = {
    "rabbitmq_host": os.getenv("RABBITMQ_HOST"),
    "rabbitmq_user": os.getenv("RABBITMQ_USER"),
    "rabbitmq_password": os.getenv("RABBITMQ_PASSWORD"),
    "rabbitmq_queue": os.getenv("RABBITMQ_QUEUE"),
    "rabbitmq_result_queue": os.getenv("RABBITMQ_RESULT_QUEUE"),
    "history_length": int(os.getenv("HISTORY_LENGTH") or "10"),
}

# Possible values: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
LOG_LEVEL = os.getenv("LOG_LEVEL")
assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
