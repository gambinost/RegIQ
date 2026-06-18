from dotenv import load_dotenv

load_dotenv()

import asyncio
import time

from langsmith import traceable
from band import Agent, Emit
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage

from core.cascade import resolve_cascade_target
from core.llm import get_balanced_llm
from core.timing import extract_timing_blocks, append_timing_block, post_heartbeat
from utils.loggers import log_info, log_success, log_error, log_warning

from agents.legal_parser.prompts import LEGAL_PARSER_SYSTEM_PROMPT


class LegalParserAdapter(SimpleAdapter):
    SUPPORTED_EMIT = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES = frozenset()

    def __init__(self):
        super().__init__()
        self._cascade_handle: str | None = None

    @traceable(run_type="chain", name="LegalParser")
    async def on_message(
        self,
        msg: PlatformMessage,
        tools,
        history,
        participants_msg: str | None,
        contacts_msg: str | None = None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        log_info(f"Legal Parser received message from {msg.sender_name}")

        content = msg.content
        if not content or not content.strip():
            log_error("Empty message, skipping")
            return

        # Extract timing blocks from incoming message
        cleaned_content, timing_blocks = extract_timing_blocks(content)

        agent_start = time.time()
        await post_heartbeat("legal_parser", "processing", room_id=room_id)

        try:
            llm = get_balanced_llm()
            response = await llm.ainvoke(
                [
                    ("system", LEGAL_PARSER_SYSTEM_PROMPT),
                    ("human", cleaned_content),
                ]
            )

            slug, cascade_handle = await resolve_cascade_target(
                tools, "legal_parser", self._cascade_handle
            )
            self._cascade_handle = cascade_handle
            mention = cascade_handle or slug or "impact-mapper"

            # Build outgoing message with cumulative timing
            chat_message = response.content
            for block in timing_blocks:
                chat_message = append_timing_block(chat_message, block["agent"], block["duration"])
            chat_message = append_timing_block(
                chat_message, "legal_parser", time.time() - agent_start
            )

            log_success(f"Parsing complete, sending to {mention}")
            await tools.send_message(
                chat_message,
                mentions=[mention],
            )
            await post_heartbeat(
                "legal_parser", "complete", time.time() - agent_start, room_id=room_id
            )

        except Exception as e:
            log_error(f"Error parsing regulation: {e}")
            try:
                slug, cascade_handle = await resolve_cascade_target(
                    tools, "legal_parser", self._cascade_handle
                )
                self._cascade_handle = cascade_handle
                mention = cascade_handle or slug or "impact-mapper"
            except Exception:
                mention = "impact-mapper"
            await tools.send_message(
                "Error parsing regulation. Please retry.",
                mentions=[mention],
            )


async def main():
    log_info("Starting Legal Parser Agent...")

    adapter = LegalParserAdapter()

    agent = Agent.from_config(
        "legal_parser",
        adapter=adapter,
        config_path=str(
            __import__("pathlib").Path(__file__).resolve().parent.parent.parent
            / "configs"
            / "agent_config.yaml"
        ),
    )

    log_success("Legal Parser Agent configured, connecting to Band...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
