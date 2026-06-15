import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from band.core.types import PlatformMessage
from band.testing.fake_tools import FakeAgentTools

from agents.monitor.agent import MonitorAdapter, format_assessment
from core.cascade import CASCADE_SLUGS, resolve_cascade_target
from models.regulation import RegulationAssessment


LEGAL_PARSER_PARTICIPANTS = [
    {
        "handle": "darkooo142/regiq-legal-parser",
        "name": "RegIQ Legal Parser",
        "id": "3c39017a-e28d-4d3c-b1e6-9d2d2aac5886",
    },
    {
        "handle": "darkooo142/regiq-monitor",
        "name": "RegIQ Monitor",
        "id": "eec2adda-854c-4cb8-b5c6-d65a65a373be",
    },
    {"handle": "darkooo142", "name": "Moamen", "id": "user-1"},
]


def _make_msg(content: str, sender_name: str = "TestUser") -> PlatformMessage:
    return PlatformMessage(
        id="msg-test-1",
        room_id="room-test",
        content=content,
        sender_id="user-1",
        sender_type="User",
        sender_name=sender_name,
        message_type="text",
        metadata=None,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_assessment() -> RegulationAssessment:
    return RegulationAssessment(
        regulation_id="GDPR-2026-003",
        regulation_name="Amendment to Article 17 - Enhanced Right to Erasure",
        jurisdiction="EU",
        effective_date="2026-09-01",
        urgency="Critical",
        urgency_reasoning="Compliance deadline within 90 days with significant penalties (4% revenue)",
        key_requirements=[
            "30-day data erasure mandate",
            "Automated deletion workflows required",
            "Audit logs of erasure operations for 3 years",
        ],
        summary="Reduces mandatory data erasure window from 90 to 30 days, requires automated workflows and audit trails.",
    )


class TestFormatAssessment:
    def test_format_contains_urgency_emoji(self, sample_assessment):
        result = format_assessment(sample_assessment)
        assert "🔴" in result
        assert "Critical" in result

    def test_format_contains_regulation_name(self, sample_assessment):
        result = format_assessment(sample_assessment)
        assert "Amendment to Article 17" in result

    def test_format_contains_jurisdiction(self, sample_assessment):
        result = format_assessment(sample_assessment)
        assert "EU" in result

    def test_format_contains_key_requirements(self, sample_assessment):
        result = format_assessment(sample_assessment)
        assert "30-day data erasure mandate" in result

    def test_format_contains_json_block(self, sample_assessment):
        result = format_assessment(sample_assessment)
        assert "```json" in result
        parsed = json.loads(result.split("```json")[1].split("```")[0].strip())
        assert parsed["regulation_id"] == "GDPR-2026-003"

    def test_format_urgency_levels(self, sample_assessment):
        for level, emoji in [("Critical", "🔴"), ("High", "🟠"), ("Medium", "🟡"), ("Low", "🟢")]:
            a = sample_assessment.model_copy(update={"urgency": level})
            result = format_assessment(a)
            assert emoji in result


class TestCascadeResolution:
    @pytest.mark.asyncio
    async def test_resolves_handle_from_participants(self):
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        slug, handle = await resolve_cascade_target(tools, "monitor")
        assert handle == "darkooo142/regiq-legal-parser"
        assert slug == "legal-parser"

    @pytest.mark.asyncio
    async def test_cache_returns_same_handle(self):
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        _, handle1 = await resolve_cascade_target(tools, "monitor", cached_handle=None)
        _, handle2 = await resolve_cascade_target(tools, "monitor", cached_handle=handle1)
        assert handle1 == handle2

    @pytest.mark.asyncio
    async def test_falls_back_when_not_found(self):
        tools = FakeAgentTools(
            participants=[
                {"handle": "darkooo142", "name": "Moamen", "id": "user-1"},
            ]
        )
        slug, handle = await resolve_cascade_target(tools, "monitor")
        assert handle == "legal-parser"

    @pytest.mark.asyncio
    async def test_finds_target_in_handle(self):
        tools = FakeAgentTools(
            participants=[
                {"handle": "someone/regiq-legal-parser", "name": "Parser", "id": "abc"},
            ]
        )
        slug, handle = await resolve_cascade_target(tools, "monitor")
        assert handle == "someone/regiq-legal-parser"

    def test_cascade_slugs_mapping(self):
        assert CASCADE_SLUGS["monitor"] == "legal-parser"
        assert CASCADE_SLUGS["legal_parser"] == "impact-mapper"
        assert CASCADE_SLUGS["impact_mapper"] == "gap-analyst"
        assert CASCADE_SLUGS["gap_analyst"] == "planner"
        assert CASCADE_SLUGS["remediation_planner"] is None


class TestMonitorAdapterOnMessage:
    @pytest.mark.asyncio
    async def test_skips_empty_message(self):
        adapter = MonitorAdapter()
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        msg = _make_msg("")

        await adapter.on_message(
            msg,
            tools,
            [],
            None,
            None,
            is_session_bootstrap=True,
            room_id="room-test",
        )

        tools.assert_no_messages_sent()

    @pytest.mark.asyncio
    async def test_skips_whitespace_only_message(self):
        adapter = MonitorAdapter()
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        msg = _make_msg("   \n\t  ")

        await adapter.on_message(
            msg,
            tools,
            [],
            None,
            None,
            is_session_bootstrap=True,
            room_id="room-test",
        )

        tools.assert_no_messages_sent()

    @pytest.mark.asyncio
    async def test_sends_assessment_with_resolved_handle(self, sample_assessment):
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=sample_assessment)

        adapter = MonitorAdapter()
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        msg = _make_msg("New GDPR regulation published")

        with patch.object(adapter, "_get_structured_llm", return_value=mock_llm):
            await adapter.on_message(
                msg,
                tools,
                [],
                None,
                None,
                is_session_bootstrap=True,
                room_id="room-test",
            )

        tools.assert_message_sent(count=1)
        sent = tools.messages_sent[0]
        assert "darkooo142/regiq-legal-parser" in sent["mentions"]
        assert "GDPR" in sent["content"]
        assert "```json" in sent["content"]

    @pytest.mark.asyncio
    async def test_mentions_legal_parser_handle(self, sample_assessment):
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=sample_assessment)

        adapter = MonitorAdapter()
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        msg = _make_msg("Regulation text here")

        with patch.object(adapter, "_get_structured_llm", return_value=mock_llm):
            await adapter.on_message(
                msg,
                tools,
                [],
                None,
                None,
                is_session_bootstrap=True,
                room_id="room-test",
            )

        tools.assert_message_sent(mentions=["darkooo142/regiq-legal-parser"])

    @pytest.mark.asyncio
    async def test_handles_llm_error_gracefully(self):
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM API error"))

        mock_retry_llm = MagicMock()
        mock_retry_llm.ainvoke = AsyncMock(side_effect=Exception("LLM API error"))

        adapter = MonitorAdapter()
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        msg = _make_msg("Some regulation text")

        with (
            patch.object(adapter, "_get_structured_llm", return_value=mock_llm),
            patch.object(adapter, "_get_retry_llm", return_value=mock_retry_llm),
        ):
            await adapter.on_message(
                msg,
                tools,
                [],
                None,
                None,
                is_session_bootstrap=True,
                room_id="room-test",
            )

        tools.assert_message_sent(count=1)
        assert "Error" in tools.messages_sent[0]["content"]
        assert len(tools.messages_sent[0]["mentions"]) >= 1

    @pytest.mark.asyncio
    async def test_retries_on_validation_error(self, sample_assessment):
        from langchain_core.exceptions import OutputParserException

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=OutputParserException("Parse error"))

        mock_retry_llm = MagicMock()
        mock_retry_llm.ainvoke = AsyncMock(return_value=sample_assessment)

        adapter = MonitorAdapter()
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        msg = _make_msg("New regulation")

        with (
            patch.object(adapter, "_get_structured_llm", return_value=mock_llm),
            patch.object(adapter, "_get_retry_llm", return_value=mock_retry_llm),
        ):
            await adapter.on_message(
                msg,
                tools,
                [],
                None,
                None,
                is_session_bootstrap=True,
                room_id="room-test",
            )

        tools.assert_message_sent(count=1)
        assert "GDPR" in tools.messages_sent[0]["content"]

    @pytest.mark.asyncio
    async def test_cascade_prompt_included(self, sample_assessment):
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=sample_assessment)

        adapter = MonitorAdapter()
        tools = FakeAgentTools(participants=LEGAL_PARSER_PARTICIPANTS)
        msg = _make_msg("Regulation update")

        with patch.object(adapter, "_get_structured_llm", return_value=mock_llm):
            await adapter.on_message(
                msg,
                tools,
                [],
                None,
                None,
                is_session_bootstrap=True,
                room_id="room-test",
            )

        from agents.monitor.prompts import URGENCY_CASCADE_PROMPT

        assert URGENCY_CASCADE_PROMPT in tools.messages_sent[0]["content"]


class TestMonitorAdapterInit:
    def test_supported_emit(self):
        adapter = MonitorAdapter()
        from band import Emit

        assert Emit.EXECUTION in adapter.SUPPORTED_EMIT

    def test_supported_capabilities_empty(self):
        adapter = MonitorAdapter()
        assert len(adapter.SUPPORTED_CAPABILITIES) == 0


class TestRegulationAssessmentModel:
    def test_assessment_creation(self, sample_assessment):
        assert sample_assessment.regulation_id == "GDPR-2026-003"
        assert sample_assessment.urgency == "Critical"
        assert len(sample_assessment.key_requirements) == 3

    def test_assessment_serialization(self, sample_assessment):
        json_str = sample_assessment.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["urgency"] == "Critical"
        assert parsed["regulation_name"] == "Amendment to Article 17 - Enhanced Right to Erasure"

    def test_assessment_defaults(self):
        a = RegulationAssessment(
            regulation_id="TEST-001",
            regulation_name="Test Regulation",
            jurisdiction="US",
            urgency="Low",
            urgency_reasoning="No immediate deadline",
            summary="Test summary",
        )
        assert a.effective_date is None
        assert a.key_requirements == []

    def test_regulation_id_auto_generated(self):
        a = RegulationAssessment(
            regulation_name="Auto ID Regulation",
            jurisdiction="EU",
            urgency="Medium",
            urgency_reasoning="Test",
            summary="Test",
        )
        assert a.regulation_id.startswith("REG-")
        assert len(a.regulation_id) == 12
