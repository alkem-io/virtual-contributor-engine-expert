from langchain.memory import ConversationBufferWindowMemory
import json
import ai_adapter
import asyncio
import os
import aio_pika
import aiormq
import json
from aio_pika import connect_robust
from config import config, LOG_LEVEL
from logger import setup_logger
from utils import clear_tags

logger = setup_logger(__name__)

logger.info(f"log level {os.path.basename(__file__)}: {LOG_LEVEL}")

# define variables
user_data = {}
user_chain = {}
# dictionary to keep track of the locks for each user
user_locks = {}
# Dictionary to keep track of the tasks for each user
user_tasks = {}
# Lock to prevent multiple ingestions from happening at the same time
ingestion_lock = asyncio.Lock()


class RabbitMQ:
    def __init__(self, host, login, password, queue):
        self.host = host
        self.login = login
        self.password = password
        self.queue = queue
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await connect_robust(
            host=self.host, login=self.login, password=self.password
        )
        self.channel = await self.connection.channel()


rabbitmq = RabbitMQ(
    host=config["rabbitmq_host"],
    login=config["rabbitmq_user"],
    password=config["rabbitmq_password"],
    queue=config["rabbitmq_queue"],
)


async def query(user_id, message_body, language_code):
    async with ingestion_lock:

        # trim the VC tag
        message_body["question"] = clear_tags(message_body["question"])

        logger.info(f"Query from user {user_id}: {message_body['question']}")

        if user_id not in user_data:
            user_data[user_id] = {}
            user_data[user_id]["chat_history"] = ConversationBufferWindowMemory(
                k=3, return_messages=True, output_key="answer", input_key="question"
            )
            reset(user_id)

        user_data[user_id]["language"] = language_code

        logger.debug(f"language: {user_data[user_id]['language']}")

        result = await ai_adapter.invoke(message_body)
        logger.debug(f"LLM result: {result}")

        user_data[user_id]["chat_history"].save_context(
            {"question": message_body["question"]},
            {"answer": result["answer"]},
        )
        logger.debug(f"new chat history {user_data[user_id]['chat_history']}")
        response = {
            "question": message_body["question"],
        } | result

        logger.info(response)

        return json.dumps(response)


def reset(user_id):
    user_data[user_id]["chat_history"].clear()
    return "Reset function executed"


async def on_request(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        # Parse the message body as JSON
        body = json.loads(message.body)

        # Get the user ID from the message body
        user_id = body["data"]["userID"]

        logger.info(f"request arriving for user id: {user_id}, deciding what to do")

        # If there's no lock for this user, create one
        if user_id not in user_locks:
            user_locks[user_id] = asyncio.Lock()

        # Check if the lock is locked
        if user_locks[user_id].locked():
            logger.info(
                f"existing task running for user id: {user_id}, waiting for it to finish first"
            )
        else:
            logger.info(f"no task running for user id: {user_id}, let's move!")

        # Acquire the lock for this user
        async with user_locks[user_id]:
            # Process the message
            await process_message(message)


async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    body = json.loads(message.body.decode())
    user_id = body["data"].get("userID")

    logger.debug(body)

    operation = body["pattern"]["cmd"]

    if user_id is None:
        response = "userID not provided"
    else:
        if operation == "query":
            if "question" in body["data"]:
                logger.info(
                    f"query time for user id: {user_id}, let's call the query() function!"
                )
                response = await query(user_id, body["data"], "English")
            else:
                response = "Query parameter(s) not provided"
        elif operation == "reset":
            response = reset(user_id)
        else:
            response = "Unknown function"

    if rabbitmq.connection and rabbitmq.channel:
        try:
            if rabbitmq.connection.is_closed or rabbitmq.channel.is_closed:
                logger.error(
                    "Connection or channel is not open. Cannot publish message."
                )
                return

            await rabbitmq.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(
                        {"operation": "feedback", "result": response}
                    ).encode(),
                    correlation_id=message.correlation_id,
                    reply_to=message.reply_to,
                ),
                routing_key=message.reply_to or "",
            )
            logger.info(f"Response sent for correlation_id: {message.correlation_id}")
            logger.info(f"Response sent to: {message.reply_to}")
            logger.debug(f"response: {response}")
        except (
            aio_pika.exceptions.AMQPError,
            asyncio.exceptions.CancelledError,
            aiormq.exceptions.ChannelInvalidStateError,
        ) as e:
            logger.error(f"Failed to publish message due to a RabbitMQ error: {e}")


async def main():
    logger.info(f"main fucntion (re)starting\n")
    # rabbitmq is an instance of the RabbitMQ class defined earlier
    await rabbitmq.connect()

    if rabbitmq.channel:
        await rabbitmq.channel.set_qos(prefetch_count=20)
        queue = await rabbitmq.channel.declare_queue(
            rabbitmq.queue, auto_delete=False, durable=True
        )

        # Start consuming messages
        asyncio.create_task(queue.consume(on_request))

        logger.info("Waiting for RPC requests")

    # Create an Event that is never set, and wait for it forever
    # This will keep the program running indefinitely
    stop_event = asyncio.Event()
    await stop_event.wait()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
