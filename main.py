import ai_adapter
import asyncio
import os
from alkemio_virtual_contributor_engine.alkemio_vc_engine import (
    AlkemioVirtualContributorEngine,
)
from alkemio_virtual_contributor_engine.events.input import Input
from alkemio_virtual_contributor_engine.events.response import Response
from config import LOG_LEVEL
from logger import setup_logger


logger = setup_logger(__name__)

logger.info(f"log level {os.path.basename(__file__)}: {LOG_LEVEL}")


async def on_request(input: Input) -> Response:
    logger.info(f"Expert engine invoked; Input is {input.dict()}")
    logger.info(
        f"AiPersonaServiceID={input.persona_id} with VC name `{input.display_name}` invoked."
    )
    result = await ai_adapter.invoke(input)
    logger.info(f"LLM result: {result.dict()}")
    return result


engine = AlkemioVirtualContributorEngine()
engine.register_handler(on_request)
asyncio.run(engine.start())
