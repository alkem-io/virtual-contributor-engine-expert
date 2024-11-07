import os

from dotenv import load_dotenv

load_dotenv()


class Env:
    def __init__(self):
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST") or ""
        self.rabbitmq_user = os.getenv("RABBITMQ_USER") or ""
        self.rabbitmq_password = os.getenv("RABBITMQ_PASSWORD") or ""
        self.rabbitmq_input_queue = os.getenv("RABBITMQ_QUEUE") or ""
        self.rabbitmq_result_queue = os.getenv("RABBITMQ_RESULT_QUEUE") or ""
        self.rabbitmq_exchange = os.getenv("RABBITMQ_EVENT_BUS_EXCHANGE") or ""
        self.rabbitmq_result_routing_key = (
            os.getenv("RABBITMQ_RESULT_ROUTING_KEY") or ""
        )


env = Env()
