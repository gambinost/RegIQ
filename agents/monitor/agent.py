import asyncio

from band import Agent, Emit
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage
from band.runtime.tools import AgentToolsProtocol

from core.llm import get_fast_llm
from models.regulation import RegulationAssessment
from utils.loggers import log_info, log_success, log_error, log_warning

from agents.monitor.prompts import MONITOR_SYSTEM_PROMPT, URGENCY_CASCADE_PROMPT

CASCADE_TARGET_SLUG = "legal-parser"


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
        self._cascade_handle: str | None = None

    def _get_structured_llm(self):
        if self._structured_llm is None:
            self._structured_llm = get_fast_llm().with_structured_output(RegulationAssessment)
        return self._structured_llm

    async def _resolve_cascade_target(self, tools: AgentToolsProtocol) -> str:
        if self._cascade_handle is not None:
            return self._cascade_handle

        try:
            participants = await tools.get_participants()
            for p in participants:
                handle = getattr(p, "handle", None) or (
                    p.get("handle", "") if isinstance(p, dict) else ""
                )
                if CASCADE_TARGET_SLUG in handle:
                    self._cascade_handle = handle
                    log_success(f"Resolved cascade target: {handle}")
                    return handle
        except Exception as e:
            log_warning(f"Could not resolve cascade target from participants: {e}")

        self._cascade_handle = CASCADE_TARGET_SLUG
        log_warning(f"Could not find '{CASCADE_TARGET_SLUG}' in participants, using fallback")
        return self._cascade_handle

    async def on_message(
        self,
        msg: PlatformMessage,
        tools: AgentToolsProtocol,
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

        try:
            structured_llm = self._get_structured_llm()

            log_info("Calling LLM for regulation assessment...")
            assessment: RegulationAssessment = await structured_llm.ainvoke(
                [
                    ("system", MONITOR_SYSTEM_PROMPT),
                    ("human", content),
                ]
            )

            log_success(f"Assessment complete: {assessment.regulation_name} — {assessment.urgency}")

            cascade_handle = await self._resolve_cascade_target(tools)
            chat_message = format_assessment(assessment) + "\n\n" + URGENCY_CASCADE_PROMPT

            await tools.send_message(chat_message, mentions=[cascade_handle])
            log_success(f"Sent assessment to room, @mentioning {cascade_handle}")

        except Exception as e:
            log_error(f"Error processing regulation: {e}")
            await tools.send_message(
                f"Error processing regulation: {e}",
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
