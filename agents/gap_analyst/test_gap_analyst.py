import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from band.core.types import PlatformMessage
from band.testing.fake_tools import FakeAgentTools

from agents.gap_analyst.agent import GapAnalystAdapter, _extract_json_block
from agents.gap_analyst.prompts import GAP_ANALYST_SYSTEM_PROMPT, GAP_ANALYST_CASCADE_PROMPT
from core.cascade import CASCADE_SLUGS, resolve_cascade_target
from models.gap import ComplianceGap, GapAnalysis


REMEDIATION_PLANNER_PARTICIPANTS = [
    {
        "handle": "darkooo142/regiq-planner",
        "name": "RegIQ Planner",
        "id": "2b38f5a1-7744-4c9e-b5d6-612e0a3b8f91",
    },
    {
        "handle": "darkooo142/regiq-gap-analyst",
        "name": "RegIQ Gap Analyst",
        "id": "1a27ae4e-95a9-401e-8d6d-50963b1488c0",
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


SAMPLE_IMPACT_TEXT = """## 🗺️ Impact Mapping — GDPR-2026-003

### REQ-003-1: 30-day data erasure mandate
- Company Process: User data deletion
- SOP: SOP-UD-001
- Current Practice: 60-day SLA with manual approval chain
- Alignment: 0.1
- Notes: Current SLA doubles the regulatory requirement

### REQ-003-2: Automated deletion workflows
- Company Process: Data deletion workflow
- SOP: SOP-UD-001
- Current Practice: Manual multi-step process
- Alignment: 0.0
- Notes: No automated deletion capability exists

### REQ-003-3: Audit trail for erasure operations
- Company Process: Audit logging
- SOP: SOP-AC-001
- Current Practice: Basic access logging only
- Alignment: 0.2
- Notes: Current logs don't capture deletion operations specifically

Overall Impact: Critical

```json
{
  "regulation_id": "GDPR-2026-003",
  "impact_mappings": [
    {
      "requirement_id": "REQ-003-1",
      "company_process": "User data deletion",
      "sop_document": "SOP-UD-001",
      "current_practice": "60-day SLA with manual approval chain",
      "alignment_score": 0.1,
      "notes": "Current SLA doubles the regulatory requirement"
    },
    {
      "requirement_id": "REQ-003-2",
      "company_process": "Data deletion workflow",
      "sop_document": "SOP-UD-001",
      "current_practice": "Manual multi-step process",
      "alignment_score": 0.0,
      "notes": "No automated deletion capability exists"
    },
    {
      "requirement_id": "REQ-003-3",
      "company_process": "Audit logging",
      "sop_document": "SOP-AC-001",
      "current_practice": "Basic access logging only",
      "alignment_score": 0.2,
      "notes": "Current logs don't capture deletion operations specifically"
    }
  ],
  "overall_impact": "Critical"
}
```"""


class TestComplianceGapModel:
    def test_gap_creation(self):
        gap = ComplianceGap(
            requirement_id="REQ-003-2",
            obligation="Must implement automated deletion within 30 days",
            current_practice="Manual multi-step process with 60-day SLA",
            gap_description="No automated deletion capability exists; SLA exceeds requirement",
            severity="Critical",
            affected_systems=["User Deletion Service", "CRM"],
        )
        assert gap.requirement_id == "REQ-003-2"
        assert gap.severity == "Critical"
        assert len(gap.affected_systems) == 2

    def test_gap_defaults(self):
        gap = ComplianceGap(
            requirement_id="REQ-1",
            obligation="Test obligation",
            current_practice="Test practice",
            gap_description="Test gap",
            severity="Low",
        )
        assert gap.affected_systems == []

    def test_gap_serialization(self):
        gap = ComplianceGap(
            requirement_id="REQ-003-1",
            obligation="Delete data within 30 days",
            current_practice="60-day SLA",
            gap_description="SLA exceeds requirement by 30 days",
            severity="Critical",
            affected_systems=["CRM"],
        )
        data = json.loads(gap.model_dump_json())
        assert data["requirement_id"] == "REQ-003-1"
        assert data["severity"] == "Critical"


class TestGapAnalysisModel:
    def test_analysis_creation(self):
        analysis = GapAnalysis(
            regulation_id="GDPR-2026-003",
            gaps=[
                ComplianceGap(
                    requirement_id="REQ-003-2",
                    obligation="Automated deletion required",
                    current_practice="Manual process",
                    gap_description="No automation",
                    severity="Critical",
                )
            ],
            total_gaps=1,
            critical_count=1,
        )
        assert analysis.regulation_id == "GDPR-2026-003"
        assert len(analysis.gaps) == 1
        assert analysis.total_gaps == 1
        assert analysis.critical_count == 1

    def test_analysis_serialization(self):
        analysis = GapAnalysis(
            regulation_id="TEST-001",
            gaps=[],
            total_gaps=0,
            critical_count=0,
        )
        data = json.loads(analysis.model_dump_json())
        assert data["regulation_id"] == "TEST-001"
        assert data["total_gaps"] == 0

    def test_severity_levels(self):
        for level in ["Low", "Medium", "High", "Critical"]:
            gap = ComplianceGap(
                requirement_id="REQ-1",
                obligation="Test",
                current_practice="Test",
                gap_description="Test",
                severity=level,
            )
            assert gap.severity == level


class TestGapAnalystPrompt:
    def test_prompt_mentions_planner(self):
        assert "Remediation Planner" in GAP_ANALYST_SYSTEM_PROMPT

    def test_prompt_mentions_json_schema(self):
        for field in [
            "requirement_id",
            "obligation",
            "current_practice",
            "gap_description",
            "severity",
            "affected_systems",
        ]:
            assert field in GAP_ANALYST_SYSTEM_PROMPT

    def test_prompt_mentions_severity_levels(self):
        for level in ["Low", "Medium", "High", "Critical"]:
            assert level in GAP_ANALYST_SYSTEM_PROMPT

    def test_prompt_mentions_alignment_scores(self):
        assert "alignment" in GAP_ANALYST_SYSTEM_PROMPT.lower()
        assert "1.0" in GAP_ANALYST_SYSTEM_PROMPT

    def test_prompt_skips_fully_compliant(self):
        assert "1.0" in GAP_ANALYST_SYSTEM_PROMPT
        assert "Skip" in GAP_ANALYST_SYSTEM_PROMPT or "skip" in GAP_ANALYST_SYSTEM_PROMPT

    def test_cascade_prompt_exists(self):
        assert (
            "Planner" in GAP_ANALYST_CASCADE_PROMPT
            or "planner" in GAP_ANALYST_CASCADE_PROMPT.lower()
        )


class TestExtractJsonBlock:
    def test_extracts_json_from_markdown(self):
        text = 'Result:\n```json\n{"key": "value"}\n```\nDone.'
        assert _extract_json_block(text) == '{"key": "value"}'

    def test_returns_full_text_when_no_json_block(self):
        text = "Just plain text, no JSON here."
        assert _extract_json_block(text) == text

    def test_extracts_multiline_json(self):
        json_content = '{\n  "regulation_id": "GDPR-2026-003",\n  "gaps": []\n}'
        text = f"Result:\n```json\n{json_content}\n```"
        assert _extract_json_block(text) == json_content


class TestCascadeResolution:
    @pytest.mark.asyncio
    async def test_resolves_handle_from_participants(self):
        tools = FakeAgentTools(participants=REMEDIATION_PLANNER_PARTICIPANTS)
        slug, handle = await resolve_cascade_target(tools, "gap_analyst")
        assert handle == "darkooo142/regiq-planner"
        assert slug == "planner"

    @pytest.mark.asyncio
    async def test_falls_back_to_slug(self):
        tools = FakeAgentTools(
            participants=[
                {"handle": "darkooo142", "name": "Moamen", "id": "user-1"},
            ]
        )
        slug, handle = await resolve_cascade_target(tools, "gap_analyst")
        assert slug == "planner"
        assert handle == "planner"

    def test_cascade_slugs_mapping(self):
        assert CASCADE_SLUGS["gap_analyst"] == "planner"
        assert CASCADE_SLUGS["impact_mapper"] == "gap-analyst"


class TestGapAnalystAdapterOnMessage:
    @pytest.mark.asyncio
    async def test_skips_empty_message(self):
        adapter = GapAnalystAdapter()
        tools = FakeAgentTools(participants=REMEDIATION_PLANNER_PARTICIPANTS)
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
        adapter = GapAnalystAdapter()
        tools = FakeAgentTools(participants=REMEDIATION_PLANNER_PARTICIPANTS)
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
    async def test_sends_gap_analysis_with_resolved_handle(self):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "## Gap Analysis\n\nCritical gaps found."
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        adapter = GapAnalystAdapter()
        tools = FakeAgentTools(participants=REMEDIATION_PLANNER_PARTICIPANTS)
        msg = _make_msg(SAMPLE_IMPACT_TEXT)

        with patch.object(adapter, "_cascade_handle", None):
            with patch("agents.gap_analyst.agent.get_balanced_llm", return_value=mock_llm):
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
        assert "darkooo142/regiq-planner" in sent["mentions"]
        assert "Critical gaps found" in sent["content"]

    @pytest.mark.asyncio
    async def test_cascade_prompt_included_in_output(self):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Gap analysis complete."
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        adapter = GapAnalystAdapter()
        tools = FakeAgentTools(participants=REMEDIATION_PLANNER_PARTICIPANTS)
        msg = _make_msg(SAMPLE_IMPACT_TEXT)

        with patch("agents.gap_analyst.agent.get_balanced_llm", return_value=mock_llm):
            await adapter.on_message(
                msg,
                tools,
                [],
                None,
                None,
                is_session_bootstrap=True,
                room_id="room-test",
            )

        assert GAP_ANALYST_CASCADE_PROMPT in tools.messages_sent[0]["content"]

    @pytest.mark.asyncio
    async def test_handles_llm_error_gracefully(self):
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM API error"))

        adapter = GapAnalystAdapter()
        tools = FakeAgentTools(participants=REMEDIATION_PLANNER_PARTICIPANTS)
        msg = _make_msg(SAMPLE_IMPACT_TEXT)

        with patch("agents.gap_analyst.agent.get_balanced_llm", return_value=mock_llm):
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
    async def test_caches_cascade_handle(self):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Gap analysis."
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        adapter = GapAnalystAdapter()
        tools = FakeAgentTools(participants=REMEDIATION_PLANNER_PARTICIPANTS)
        msg = _make_msg(SAMPLE_IMPACT_TEXT)

        with patch("agents.gap_analyst.agent.get_balanced_llm", return_value=mock_llm):
            await adapter.on_message(
                msg,
                tools,
                [],
                None,
                None,
                is_session_bootstrap=True,
                room_id="room-test",
            )

        assert adapter._cascade_handle == "darkooo142/regiq-planner"

    @pytest.mark.asyncio
    async def test_uses_human_message_with_impact_data(self):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Gap analysis result."
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        adapter = GapAnalystAdapter()
        tools = FakeAgentTools(participants=REMEDIATION_PLANNER_PARTICIPANTS)
        msg = _make_msg(SAMPLE_IMPACT_TEXT)

        with patch("agents.gap_analyst.agent.get_balanced_llm", return_value=mock_llm):
            await adapter.on_message(
                msg,
                tools,
                [],
                None,
                None,
                is_session_bootstrap=True,
                room_id="room-test",
            )

        call_args = mock_llm.ainvoke.call_args
        messages = call_args[0][0]
        assert messages[0][0] == "system"
        assert messages[1][0] == "human"
        assert "Impact Mapping Data" in messages[1][1]
        assert "REQ-003-1" in messages[1][1]


class TestGapAnalystAdapterInit:
    def test_supported_emit(self):
        adapter = GapAnalystAdapter()
        from band import Emit

        assert Emit.EXECUTION in adapter.SUPPORTED_EMIT

    def test_supported_capabilities_empty(self):
        adapter = GapAnalystAdapter()
        assert len(adapter.SUPPORTED_CAPABILITIES) == 0

    def test_cascade_handle_initially_none(self):
        adapter = GapAnalystAdapter()
        assert adapter._cascade_handle is None
