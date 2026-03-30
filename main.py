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

input_exclude = {"prompt_graph"}


async def on_request(input: Input) -> Response:
    logger.info(
        f"AiPersonaID={input.persona_id} "
        f"VC=`{input.display_name}` "
        f"query=`{input.message}` "
        f"history_count={len(input.history)}"
    )
    logger.debug(f"Full input: {input.model_dump(exclude=input_exclude)}")

    result = await ai_adapter.invoke(input)

    source_count = len(result.sources) if result.sources else 0
    logger.info(
        f"Response: answer_length={len(result.result)} "
        f"sources={source_count} "
        f"language={result.human_language}"
    )
    logger.debug(f"Full response: {result.model_dump()}")

    return result


engine = AlkemioVirtualContributorEngine()
engine.register_handler(on_request)
asyncio.run(engine.start())
