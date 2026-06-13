from __future__ import annotations

import logging
from typing import Any

from band.converters.langchain import LangChainHistoryConverter, LangChainMessages
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

logger = logging.getLogger(__name__)

MAX_TOOL_NAME_LENGTH = 200


class SanitizingHistoryConverter(LangChainHistoryConverter):
    """LangChain history converter that strips tool_calls with names
    exceeding Anthropic's 200-character limit.

    Prevents ``openai.BadRequestError: tool_use.name: String should have at
    most 200 characters`` when polluted room history contains oversized
    tool names (e.g. from ``with_structured_output`` without ``method="json_mode"``).
    """

    def convert(self, raw: list[dict[str, Any]]) -> LangChainMessages:
        messages = super().convert(raw)
        logger.debug(
            "[SANITIZE-DEBUG] convert() produced %d messages from %d raw events",
            len(messages),
            len(raw),
        )
        for i, raw_event in enumerate(raw):
            mt = raw_event.get("message_type", "unknown")
            name = raw_event.get("name", "")
            content_preview = str(raw_event.get("content", ""))[:120]
            logger.debug(
                "[SANITIZE-DEBUG] raw[%d]: type=%s name=%r content=%.120s",
                i,
                mt,
                name,
                content_preview,
            )
        return self._sanitize(messages)

    @staticmethod
    def _sanitize(messages: LangChainMessages) -> LangChainMessages:
        bad_ids: set[str] = set()
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "")
                    name_len = len(name)
                    logger.info(
                        "[SANITIZE-DEBUG] msg[%d] AIMessage tool_call: name=%r (%d chars) id=%s",
                        i,
                        name[:80],
                        name_len,
                        tc.get("id", "?"),
                    )
                    if name_len > MAX_TOOL_NAME_LENGTH:
                        tc_id: str = tc.get("id") or ""
                        bad_ids.add(tc_id)
                        logger.warning(
                            "[SANITIZE-DEBUG] OVERSIZED tool_call id=%s name=%r (%d chars, limit %d) — will strip",
                            tc_id,
                            name[:300],
                            name_len,
                            MAX_TOOL_NAME_LENGTH,
                        )
            elif isinstance(msg, AIMessage):
                content_preview = str(msg.content)[:120] if msg.content else ""
                logger.debug(
                    "[SANITIZE-DEBUG] msg[%d] AIMessage (no tool_calls): content=%.120s",
                    i,
                    content_preview,
                )
            elif isinstance(msg, ToolMessage):
                logger.debug(
                    "[SANITIZE-DEBUG] msg[%d] ToolMessage: name=%s tool_call_id=%s content=%.80s",
                    i,
                    getattr(msg, "name", "?"),
                    msg.tool_call_id,
                    str(msg.content)[:80],
                )
            elif isinstance(msg, HumanMessage):
                content_preview = str(msg.content)[:120] if msg.content else ""
                logger.debug(
                    "[SANITIZE-DEBUG] msg[%d] HumanMessage: content=%.120s",
                    i,
                    content_preview,
                )
            else:
                logger.debug(
                    "[SANITIZE-DEBUG] msg[%d] %s: content=%.80s",
                    i,
                    type(msg).__name__,
                    str(getattr(msg, "content", ""))[:80],
                )

        if not bad_ids:
            logger.info("[SANITIZE-DEBUG] No oversized tool calls found — returning messages as-is")
            return messages

        logger.warning(
            "[SANITIZE-DEBUG] Stripping %d oversized tool calls (bad_ids=%s)",
            len(bad_ids),
            bad_ids,
        )
        cleaned: LangChainMessages = []
        for msg in messages:
            if isinstance(msg, ToolMessage):
                if msg.tool_call_id in bad_ids:
                    logger.info(
                        "[SANITIZE-DEBUG] Stripping ToolMessage with tool_call_id=%s",
                        msg.tool_call_id,
                    )
                    continue
                cleaned.append(msg)
            elif isinstance(msg, AIMessage):
                if msg.tool_calls:
                    kept = [tc for tc in msg.tool_calls if tc.get("id") not in bad_ids]
                    if kept:
                        cleaned.append(AIMessage(content=msg.content, tool_calls=kept))
                    elif msg.content:
                        cleaned.append(AIMessage(content=msg.content))
                else:
                    cleaned.append(msg)
            else:
                cleaned.append(msg)

        logger.info(
            "[SANITIZE-DEBUG] Sanitized %d messages → %d messages",
            len(messages),
            len(cleaned),
        )
        return cleaned
