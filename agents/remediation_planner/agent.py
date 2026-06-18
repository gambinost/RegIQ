from dotenv import load_dotenv

load_dotenv()

import asyncio
import json
import time

from band import Agent, Emit
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage

from core.llm import get_balanced_llm
from core.settings import get_settings
from core.timing import (
    extract_timing_blocks,
    build_timing_dict,
    append_timing_block,
    format_timing_for_display,
    post_heartbeat,
)
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


async def _resolve_human_handle(tools) -> str | None:
    try:
        participants = await tools.get_participants()
        for p in participants:
            handle = getattr(p, "handle", None) or (
                p.get("handle", "") if isinstance(p, dict) else ""
            )
            if handle and "/regiq-" not in handle:
                return handle
    except Exception:
        pass
    return None


async def _resolve_self_handle(tools) -> str | None:
    """Find the Planner's own handle from room participants.

    Used to @mention itself when posting the final remediation report to
    the Band chat — there's no human to @mention in API-triggered rooms,
    so the Planner posts to itself to make the report visible in the
    Band chat UI. The self-message guard at the top of on_message
    prevents re-processing.
    """
    try:
        participants = await tools.get_participants()
        for p in participants:
            handle = getattr(p, "handle", None) or (
                p.get("handle", "") if isinstance(p, dict) else ""
            )
            if handle and "regiq-planner" in handle.lower():
                return handle
    except Exception:
        pass
    return None


class RemediationPlannerAdapter(SimpleAdapter):
    SUPPORTED_EMIT = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES = frozenset()

    def __init__(self):
        super().__init__()
        self._human_handle: str | None = None
        self._self_handle: str | None = None

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

        # Self-message guard: skip messages from ourselves.
        # When no human is in the room, the Planner @mentions itself to
        # post the final report to the Band chat. Without this guard,
        # that self-mention would re-trigger on_message → infinite loop.
        sender_lower = (msg.sender_name or "").lower()
        if "planner" in sender_lower:
            log_info("Self-message detected, skipping (report already posted to Band chat)")
            return

        if not self._human_handle:
            self._human_handle = await _resolve_human_handle(tools)
        if not self._self_handle:
            self._self_handle = await _resolve_self_handle(tools)
        mention = self._human_handle

        content = msg.content
        if not content or not content.strip():
            log_error("Empty message, skipping")
            return

        # Extract timing blocks from all upstream agents
        cleaned_content, timing_blocks = extract_timing_blocks(content)

        agent_start = time.time()
        await post_heartbeat("remediation_planner", "processing", room_id=room_id)

        try:
            llm = get_balanced_llm()

            human_message = f"## Gap Analysis Data\n{cleaned_content}"

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

            # Add own timing to the collection
            planner_duration = round(time.time() - agent_start, 2)
            timing_blocks.append({"agent": "remediation_planner", "duration": planner_duration})
            timing_dict = build_timing_dict(timing_blocks)
            if timing_dict:
                log_info(format_timing_for_display(timing_dict))

            try:
                report_data = json.loads(json_str)
                report = ComplianceReport.model_validate(report_data)
                # Inject timing into report
                if timing_dict:
                    report.timing = timing_dict
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

            chat_message = raw + PLANNER_TERMINAL_PROMPT

            log_success("Remediation plan complete — terminal agent, no cascade")
            if mention:
                await tools.send_message(chat_message, mentions=[mention])
            elif self._self_handle:
                # No human in room (API-triggered run). @mention ourselves
                # to post the final report to the Band chat so it's visible
                # in the UI. The self-message guard prevents re-processing.
                log_info("No human in room — posting report to Band chat via self-mention")
                await tools.send_message(chat_message, mentions=[self._self_handle])
            else:
                log_warning(
                    "No human or self handle found — report delivered via API only, "
                    "not visible in Band chat"
                )
            await post_heartbeat(
                "remediation_planner", "complete", time.time() - agent_start, room_id=room_id
            )

        except Exception as e:
            log_error(f"Error generating remediation plan: {e}")
            error_mention = mention or self._self_handle
            if error_mention:
                await tools.send_message(
                    "Error generating remediation plan. Please retry.",
                    mentions=[error_mention],
                )


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
