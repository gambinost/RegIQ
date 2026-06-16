from dotenv import load_dotenv

load_dotenv()

import asyncio
import json
import re

from band import Agent, Emit
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage

from core.llm import get_balanced_llm
from core.settings import get_settings
from models.report import ComplianceReport
from utils.loggers import log_info, log_success, log_error, log_warning

try:
    import httpx
except ImportError:
    httpx = None

from agents.remediation_planner.prompts import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_TERMINAL_PROMPT,
)


def _extract_json(text: str) -> str:
    brace = text.find("{")
    if brace == -1:
        return text
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[brace : i + 1]
    return text[brace:]


class RemediationPlannerAdapter(SimpleAdapter):
    SUPPORTED_EMIT = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES = frozenset()

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
        log_info(f"Remediation Planner received message from {msg.sender_name}")

        content = msg.content
        if not content or not content.strip():
            log_error("Empty message, skipping")
            return

        try:
            llm = get_balanced_llm()

            human_message = f"## Gap Analysis Data\n{content}"

            response = await llm.ainvoke(
                [
                    ("system", PLANNER_SYSTEM_PROMPT),
                    ("human", human_message),
                ]
            )

            raw = response.content
            if isinstance(raw, list):
                raw = " ".join(str(part) for part in raw)

            json_str = _extract_json(raw)

            try:
                report_data = json.loads(json_str)
                report = ComplianceReport.model_validate(report_data)
                log_success(
                    f"Validated report: {report.regulation_id} — "
                    f"{len(report.tickets)} tickets, "
                    f"{report.critical_path_weeks}wk critical path"
                )
            except (json.JSONDecodeError, Exception) as e:
                log_warning(f"JSON validation failed, sending raw output: {e}")
                report = None

            if report and httpx is not None:
                try:
                    settings = get_settings()
                    api_url = (
                        f"{settings.REGIQ_API_BASE_URL}/api/v1/hitl/report/{report.regulation_id}"
                    )
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            api_url,
                            json=report.model_dump(),
                            timeout=30.0,
                        )
                        if resp.status_code == 200:
                            log_success(f"Report submitted to API: {api_url}")
                        else:
                            log_warning(f"API returned {resp.status_code}: {resp.text}")
                except Exception as e:
                    log_warning(f"Could not submit report to API: {e}")

            if report:
                chat_message = raw.split("\n", 3)[0] if "\n" in raw else raw
                chat_message = raw
            else:
                chat_message = raw

            chat_message += PLANNER_TERMINAL_PROMPT

            log_success("Remediation plan complete — terminal agent, no cascade")
            await tools.send_message(chat_message)

        except Exception as e:
            log_error(f"Error generating remediation plan: {e}")
            await tools.send_message("Error generating remediation plan. Please retry.")


async def main():
    log_info("Starting Remediation Planner Agent...")

    adapter = RemediationPlannerAdapter()

    agent = Agent.from_config(
        "remediation_planner",
        adapter=adapter,
        config_path=str(
            __import__("pathlib").Path(__file__).resolve().parent.parent.parent
            / "configs"
            / "agent_config.yaml"
        ),
    )

    log_success("Remediation Planner Agent configured, connecting to Band...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
