from dotenv import load_dotenv

load_dotenv()

import asyncio
import re

from band import Agent, Emit
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage

from core.cascade import resolve_cascade_target
from core.llm import get_balanced_llm
from utils.loggers import log_info, log_success, log_error, log_warning

from agents.gap_analyst.prompts import GAP_ANALYST_SYSTEM_PROMPT, GAP_ANALYST_CASCADE_PROMPT


def _extract_json_block(text: str) -> str:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


class GapAnalystAdapter(SimpleAdapter):
    SUPPORTED_EMIT = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES = frozenset()

    def __init__(self):
        super().__init__()
        self._cascade_handle: str | None = None

    async def on_message(
        self,
        msg: PlatformMessage,
        tools,
        history,
        participants_msg: str | None,
        contacts_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        log_info(f"Gap Analyst received message from {msg.sender_name}")

        content = msg.content
        if not content or not content.strip():
            log_error("Empty message, skipping")
            return

        try:
            llm = get_balanced_llm()

            human_message = f"## Impact Mapping Data\n{content}"

            response = await llm.ainvoke(
                [
                    ("system", GAP_ANALYST_SYSTEM_PROMPT),
                    ("human", human_message),
                ]
            )

            slug, cascade_handle = await resolve_cascade_target(
                tools, "gap_analyst", self._cascade_handle
            )
            self._cascade_handle = cascade_handle
            mention = cascade_handle or slug or "planner"

            chat_message = response.content + GAP_ANALYST_CASCADE_PROMPT

            log_success(f"Gap analysis complete, sending to {mention}")
            await tools.send_message(chat_message, mentions=[mention])

        except Exception as e:
            log_error(f"Error analyzing gaps: {e}")
            try:
                slug, cascade_handle = await resolve_cascade_target(
                    tools, "gap_analyst", self._cascade_handle
                )
                self._cascade_handle = cascade_handle
                mention = cascade_handle or slug or "planner"
            except Exception:
                mention = "planner"
            await tools.send_message(
                "Error analyzing gaps. Please retry.",
                mentions=[mention],
            )


async def main():
    log_info("Starting Gap Analyst Agent...")

    adapter = GapAnalystAdapter()

    agent = Agent.from_config(
        "gap_analyst",
        adapter=adapter,
        config_path=str(
            __import__("pathlib").Path(__file__).resolve().parent.parent.parent
            / "configs"
            / "agent_config.yaml"
        ),
    )

    log_success("Gap Analyst Agent configured, connecting to Band...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
