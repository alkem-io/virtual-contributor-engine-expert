import asyncio
from collections.abc import Callable, Coroutine
import json
from typing import Any

from aio_pika.abc import AbstractIncomingMessage

from alkemio_virtual_contributor_engine.config import env
from alkemio_virtual_contributor_engine.events.input import Input
from alkemio_virtual_contributor_engine.events.result import Response
from alkemio_virtual_contributor_engine.rabbitmq import RabbitMQ
from logger import setup_logger


logger = setup_logger(__name__)


class AlkemioVirtualContributorEngine:

    def __init__(self):
        self.rabbitmq = RabbitMQ()
        self.handler = None

    async def start(self):
        await self.rabbitmq.connect()
        if self.invoke_handler is not None:
            await self.rabbitmq.consume(self.invoke_handler)
        await asyncio.Future()

    async def invoke_handler(self, message: AbstractIncomingMessage):
        logger.info("New message recieved.")
        if not self.handler is None:
            async with message.process():
                body = json.loads(json.loads(message.body.decode()))
                input = Input(body["input"])

                response = await self.handler(input)

                await self.rabbitmq.publish(
                    {"response": response.to_dict(), "original": input.to_dict()}
                )

                logger.info("Response for {message.correlation_id} published")

    def register_handler(
        self, handler: Callable[[Input], Coroutine[Any, Any, Response]]
    ):
        self.handler = handler
