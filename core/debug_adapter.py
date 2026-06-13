from __future__ import annotations

import logging
from typing import Any

from band.adapters import LangGraphAdapter
from band.core.types import PlatformMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

logger = logging.getLogger(__name__)

MAX_TOOL_NAME_LENGTH = 200


class LLMDebugCallback(BaseCallbackHandler):
    """LangChain callback handler that logs every message before it goes
    to the LLM. This is the standard way to intercept messages in LangChain
    and captures the exact payload that causes API errors.

    Install this callback on the LLM via:
        llm = get_balanced_llm().with_config(callbacks=[LLMDebugCallback()])
    """

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        for msg_list in messages:
            logger.info("[LLM-DEBUG] on_chat_model_start: %d messages", len(msg_list))
            for i, msg in enumerate(msg_list):
                self._log_message(i, msg)

    def _log_message(self, i: int, msg: Any) -> None:
        if isinstance(msg, AIMessage):
            if msg.tool_calls:
                for j, tc in enumerate(msg.tool_calls):
                    tc_name = tc.get("name", "")
                    tc_id = tc.get("id", "?")
                    logger.info(
                        "[LLM-DEBUG] msg[%d] AIMessage tool_calls[%d]: name=%r (%d chars) id=%s",
                        i,
                        j,
                        tc_name[:80],
                        len(tc_name),
                        tc_id,
                    )
                    if len(tc_name) > MAX_TOOL_NAME_LENGTH:
                        logger.warning(
                            "[LLM-DEBUG] OVERSIZED!!! msg[%d] tool_calls[%d] "
                            "name=%r (%d chars, limit %d) FULL_NAME_FIRST_500=%r",
                            i,
                            j,
                            tc_name[:80],
                            len(tc_name),
                            MAX_TOOL_NAME_LENGTH,
                            tc_name[:500],
                        )
                content_preview = str(msg.content)[:100] if msg.content else ""
                logger.info(
                    "[LLM-DEBUG] msg[%d] AIMessage: tool_calls=%d content=%.100s",
                    i,
                    len(msg.tool_calls),
                    content_preview,
                )
            else:
                content_preview = str(msg.content)[:120] if msg.content else ""
                logger.info(
                    "[LLM-DEBUG] msg[%d] AIMessage (no tool_calls): %.120s",
                    i,
                    content_preview,
                )
        elif isinstance(msg, ToolMessage):
            logger.info(
                "[LLM-DEBUG] msg[%d] ToolMessage: name=%s tool_call_id=%s content=%.80s",
                i,
                getattr(msg, "name", "?"),
                msg.tool_call_id,
                str(msg.content)[:80],
            )
        elif isinstance(msg, HumanMessage):
            content_preview = str(msg.content)[:120] if msg.content else ""
            logger.info(
                "[LLM-DEBUG] msg[%d] HumanMessage: %.120s",
                i,
                content_preview,
            )
        else:
            content_preview = (
                str(getattr(msg, "content", ""))[:120] if hasattr(msg, "content") else ""
            )
            logger.info(
                "[LLM-DEBUG] msg[%d] %s: %.120s",
                i,
                type(msg).__name__,
                content_preview,
            )


class DebugLangGraphAdapter(LangGraphAdapter):
    """LangGraphAdapter subclass that logs all messages at the adapter boundary.

    Logs history messages received by on_message(), plus participants and
    contacts metadata. Used alongside LLMDebugCallback for full-stack debugging.
    """

    async def on_message(
        self,
        msg: PlatformMessage,
        tools: Any,
        history: Any,
        participants_msg: str | None,
        contacts_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        logger.info(
            "[ADAPTER-DEBUG] on_message called: msg.id=%s room_id=%s "
            "is_session_bootstrap=%s history_len=%d",
            getattr(msg, "id", "?"),
            room_id,
            is_session_bootstrap,
            len(history) if history else 0,
        )

        logger.info(
            "[ADAPTER-DEBUG] participants_msg=%.80s contacts_msg=%.80s msg_content=%.100s",
            str(participants_msg)[:80] if participants_msg else None,
            str(contacts_msg)[:80] if contacts_msg else None,
            str(msg.content)[:100] if hasattr(msg, "content") else "?",
        )

        if history:
            for i, h in enumerate(history):
                if isinstance(h, AIMessage) and h.tool_calls:
                    for j, tc in enumerate(h.tool_calls):
                        tc_name = tc.get("name", "")
                        logger.info(
                            "[ADAPTER-DEBUG] history[%d] AIMessage tool_calls[%d]: "
                            "name=%r (%d chars) id=%s",
                            i,
                            j,
                            tc_name[:80],
                            len(tc_name),
                            tc.get("id", "?"),
                        )
                        if len(tc_name) > MAX_TOOL_NAME_LENGTH:
                            logger.warning(
                                "[ADAPTER-DEBUG] OVERSIZED in history: name=%r (%d chars) FULL=%r",
                                tc_name[:80],
                                len(tc_name),
                                tc_name[:500],
                            )
                elif isinstance(h, ToolMessage):
                    logger.info(
                        "[ADAPTER-DEBUG] history[%d] ToolMessage: name=%s tool_call_id=%s",
                        i,
                        getattr(h, "name", "?"),
                        h.tool_call_id,
                    )

        await super().on_message(
            msg,
            tools,
            history,
            participants_msg,
            contacts_msg,
            is_session_bootstrap=is_session_bootstrap,
            room_id=room_id,
        )

        logger.info("[ADAPTER-DEBUG] on_message completed for room %s", room_id)
