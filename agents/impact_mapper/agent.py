from dotenv import load_dotenv

load_dotenv()

import asyncio
import re
import time

from langsmith import traceable
from band import Agent, Emit
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage

from core.cascade import resolve_cascade_target
from core.llm import get_balanced_llm
from core.timing import extract_timing_blocks, append_timing_block, post_heartbeat
from rag.retriever import query_knowledge_base
from utils.loggers import log_info, log_success, log_error, log_warning

from agents.impact_mapper.prompts import IMPACT_MAPPER_SYSTEM_PROMPT, IMPACT_MAPPER_CASCADE_PROMPT


def _extract_json_block(text: str) -> str:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


class ImpactMapperAdapter(SimpleAdapter):
    SUPPORTED_EMIT = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES = frozenset()

    def __init__(self):
        super().__init__()
        self._cascade_handle: str | None = None

    @traceable(run_type="chain", name="ImpactMapper")
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
        log_info(f"Impact Mapper received message from {msg.sender_name}")

        content = msg.content
        if not content or not content.strip():
            log_error("Empty message, skipping")
            return

        # Extract timing blocks from incoming message
        cleaned_content, timing_blocks = extract_timing_blocks(content)

        agent_start = time.time()
        await post_heartbeat("impact_mapper", "processing", room_id=room_id)

        try:
            rag_context = await query_knowledge_base(cleaned_content)
            if rag_context:
                log_success(f"RAG: Retrieved context ({len(rag_context)} chars)")
            else:
                log_warning("RAG: No context retrieved, proceeding without company data")

            llm = get_balanced_llm()

            human_message = f"## Requirements\n{cleaned_content}"
            if rag_context:
                human_message += f"\n\n## Company Processes\n{rag_context}"

            response = await llm.ainvoke(
                [
                    ("system", IMPACT_MAPPER_SYSTEM_PROMPT),
                    ("human", human_message),
                ]
            )

            slug, cascade_handle = await resolve_cascade_target(
                tools, "impact_mapper", self._cascade_handle
            )
            self._cascade_handle = cascade_handle
            mention = cascade_handle or slug or "gap-analyst"

            # Build outgoing message with cumulative timing
            chat_message = response.content + IMPACT_MAPPER_CASCADE_PROMPT
            for block in timing_blocks:
                chat_message = append_timing_block(chat_message, block["agent"], block["duration"])
            chat_message = append_timing_block(
                chat_message, "impact_mapper", time.time() - agent_start
            )

            log_success(f"Impact mapping complete, sending to {mention}")
            await tools.send_message(chat_message, mentions=[mention])
            await post_heartbeat(
                "impact_mapper", "complete", time.time() - agent_start, room_id=room_id
            )

        except Exception as e:
            log_error(f"Error mapping impact: {e}")
            try:
                slug, cascade_handle = await resolve_cascade_target(
                    tools, "impact_mapper", self._cascade_handle
                )
                self._cascade_handle = cascade_handle
                mention = cascade_handle or slug or "gap-analyst"
            except Exception:
                mention = "gap-analyst"
            await tools.send_message(
                "Error mapping impact. Please retry.",
                mentions=[mention],
            )


async def main():
    log_info("Starting Impact Mapper Agent...")

    adapter = ImpactMapperAdapter()

    agent = Agent.from_config(
        "impact_mapper",
        adapter=adapter,
        config_path=str(
            __import__("pathlib").Path(__file__).resolve().parent.parent.parent
            / "configs"
            / "agent_config.yaml"
        ),
    )

    log_success("Impact Mapper Agent configured, connecting to Band...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
