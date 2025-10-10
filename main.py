import os
import asyncio
from config import LOG_LEVEL
from alkemio_virtual_contributor_engine.alkemio_vc_engine import (
    setup_logger,
    AlkemioVirtualContributorEngine,
    Response,
    Input
)

import ai_adapter


logger = setup_logger(__name__)

logger.info(f"log level {os.path.basename(__file__)}: {LOG_LEVEL}")

input_exclude = {}
if LOG_LEVEL != "DEBUG":
    input_exclude = {"prompt_graph"}


async def on_request(input: Input) -> Response:
    logger.info(f"Expert engine invoked; Input is {input.model_dump(exclude=input_exclude)}")
    logger.info(
        f"AiPersonaID={input.persona_id} with VC name `{input.display_name}` invoked."
    )
    result = await ai_adapter.invoke(input)
    logger.info(f"LLM result: {result.model_dump()}")
    return result


engine = AlkemioVirtualContributorEngine()
engine.register_handler(on_request)
asyncio.run(engine.start())
