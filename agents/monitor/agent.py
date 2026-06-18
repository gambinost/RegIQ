from dotenv import load_dotenv

load_dotenv()  # noqa: E402 — must run before langchain/langsmith imports

import asyncio  # noqa: E402
import time  # noqa: E402

from langsmith import traceable  # noqa: E402
from band import Agent, Emit  # noqa: E402
from band.core.simple_adapter import SimpleAdapter  # noqa: E402
from band.core.types import PlatformMessage  # noqa: E402
from langchain_core.exceptions import OutputParserException  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from core.cascade import resolve_cascade_target  # noqa: E402
from core.llm import get_fast_llm  # noqa: E402
from core.timing import append_timing_block, post_heartbeat  # noqa: E402
from models.regulation import RegulationAssessment  # noqa: E402
from utils.loggers import log_info, log_success, log_error, log_warning  # noqa: E402

from agents.monitor.prompts import (
    MONITOR_SYSTEM_PROMPT,
    RETRY_SYSTEM_PROMPT,
    URGENCY_CASCADE_PROMPT,
)  # noqa: E402


def format_assessment(assessment: RegulationAssessment) -> str:
    urg_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    emoji = urg_emoji.get(assessment.urgency, "⚪")
    lines = [
        f"## {emoji} Regulation Assessment — {assessment.urgency}",
        f"**Regulation:** {assessment.regulation_name}",
        f"**Jurisdiction:** {assessment.jurisdiction}",
        f"**Effective Date:** {assessment.effective_date or 'Not specified'}",
        f"**Urgency Reasoning:** {assessment.urgency_reasoning}",
        "",
        "### Key Requirements:",
    ]
    for req in assessment.key_requirements:
        lines.append(f"- {req}")
    lines.append("")
    lines.append(f"**Summary:** {assessment.summary}")
    lines.append("")
    lines.append("---")
    lines.append("```json")
    lines.append(assessment.model_dump_json(indent=2))
    lines.append("```")
    return "\n".join(lines)


class MonitorAdapter(SimpleAdapter):
    SUPPORTED_EMIT = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES = frozenset()

    def __init__(self):
        super().__init__()
        self._structured_llm = None
        self._retry_llm = None
        self._cascade_handle: str | None = None

    def _get_structured_llm(self):
        if self._structured_llm is None:
            self._structured_llm = get_fast_llm().with_structured_output(
                RegulationAssessment, method="json_mode"
            )
        return self._structured_llm

    def _get_retry_llm(self):
        if self._retry_llm is None:
            self._retry_llm = get_fast_llm().with_structured_output(
                RegulationAssessment, method="json_mode"
            )
        return self._retry_llm

    @traceable(run_type="llm", name="Monitor")
    async def _invoke_with_retry(self, content: str) -> RegulationAssessment:
        structured_llm = self._get_structured_llm()

        log_info("Calling LLM for regulation assessment...")
        try:
            assessment: RegulationAssessment = await structured_llm.ainvoke(
                [("system", MONITOR_SYSTEM_PROMPT), ("human", content)]
            )
            return assessment
        except (OutputParserException, ValidationError) as e:
            log_warning(f"First attempt failed: {e}. Retrying with stricter prompt...")
            retry_llm = self._get_retry_llm()
            assessment = await retry_llm.ainvoke(
                [("system", RETRY_SYSTEM_PROMPT), ("human", content)]
            )
            return assessment

    @traceable(run_type="chain", name="Monitor")
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
        log_info(f"Monitor received message from {msg.sender_name} in room {room_id}")

        content = msg.content
        if not content or not content.strip():
            log_error("Received empty message, skipping")
            return

        agent_start = time.time()
        await post_heartbeat("monitor", "processing", room_id=room_id)

        try:
            assessment = await self._invoke_with_retry(content)

            log_success(f"Assessment complete: {assessment.regulation_name} — {assessment.urgency}")

            slug, cascade_handle = await resolve_cascade_target(
                tools, "monitor", self._cascade_handle
            )
            self._cascade_handle = cascade_handle
            mention = cascade_handle or slug

            chat_message = format_assessment(assessment)
            chat_message += "\n\n---\n### Original Regulation Text\n\n"
            chat_message += content
            chat_message += "\n\n" + URGENCY_CASCADE_PROMPT
            chat_message = append_timing_block(chat_message, "monitor", time.time() - agent_start)

            await tools.send_message(chat_message, mentions=[mention])
            await post_heartbeat("monitor", "complete", time.time() - agent_start, room_id=room_id)
            log_success(f"Sent assessment to room, @mentioning {mention}")

        except Exception as e:
            log_error(f"Error processing regulation: {e}")
            try:
                slug, cascade_handle = await resolve_cascade_target(
                    tools, "monitor", self._cascade_handle
                )
                self._cascade_handle = cascade_handle
                mention = cascade_handle or slug
            except Exception:
                mention = "regiq-legal-parser"
            await tools.send_message(
                f"Error processing regulation. Please retry.",
                mentions=[mention],
            )


async def main():
    log_info("Starting Monitor Agent...")
    adapter = MonitorAdapter()

    agent = Agent.from_config(
        "monitor",
        adapter=adapter,
        config_path=str(
            __import__("pathlib").Path(__file__).resolve().parent.parent.parent
            / "configs"
            / "agent_config.yaml"
        ),
    )

    log_success("Monitor Agent configured, connecting to Band...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
