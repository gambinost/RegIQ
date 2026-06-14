import json

import pytest

from models.impact import ImpactMapping, ImpactAssessment


GAP_ANALYST_PARTICIPANTS = [
    {
        "handle": "darkooo142/regiq-gap-analyst",
        "name": "RegIQ Gap Analyst",
        "id": "1a27ae4e-95a9-401e-8d6d-50963b1488c0",
    },
    {
        "handle": "darkooo142/regiq-impact-mapper",
        "name": "RegIQ Impact Mapper",
        "id": "be3f4dd3-4344-4983-9679-943df9f86647",
    },
    {"handle": "darkooo142", "name": "Moamen", "id": "user-1"},
]


class TestImpactMappingModel:
    def test_impact_mapping_creation(self):
        mapping = ImpactMapping(
            requirement_id="REQ-GDPR-2026-003-1",
            company_process="User data deletion",
            sop_document="SOP-UD-001",
            current_practice="60-day SLA with manual approval chain",
            alignment_score=0.2,
            notes="Current 60-day SLA exceeds 30-day mandate",
        )
        assert mapping.requirement_id == "REQ-GDPR-2026-003-1"
        assert mapping.alignment_score == 0.2

    def test_alignment_score_bounds(self):
        ImpactMapping(
            requirement_id="REQ-1",
            company_process="test",
            sop_document="SOP-X",
            current_practice="test",
            alignment_score=0.0,
            notes="",
        )
        ImpactMapping(
            requirement_id="REQ-1",
            company_process="test",
            sop_document="SOP-X",
            current_practice="test",
            alignment_score=1.0,
            notes="",
        )

    def test_alignment_score_rejects_above_one(self):
        with pytest.raises(Exception):
            ImpactMapping(
                requirement_id="REQ-1",
                company_process="test",
                sop_document="SOP-X",
                current_practice="test",
                alignment_score=1.5,
            )

    def test_alignment_score_rejects_below_zero(self):
        with pytest.raises(Exception):
            ImpactMapping(
                requirement_id="REQ-1",
                company_process="test",
                sop_document="SOP-X",
                current_practice="test",
                alignment_score=-0.1,
            )

    def test_impact_mapping_serialization(self):
        mapping = ImpactMapping(
            requirement_id="REQ-1",
            company_process="Deletion",
            sop_document="SOP-UD-001",
            current_practice="60-day manual process",
            alignment_score=0.25,
            notes="Major gap",
        )
        data = json.loads(mapping.model_dump_json())
        assert data["requirement_id"] == "REQ-1"
        assert data["alignment_score"] == 0.25

    def test_impact_mapping_defaults(self):
        mapping = ImpactMapping(
            requirement_id="REQ-1",
            company_process="test",
            sop_document="SOP-X",
            current_practice="test",
            alignment_score=0.5,
        )
        assert mapping.notes == ""


class TestImpactAssessmentModel:
    def test_assessment_creation(self):
        assessment = ImpactAssessment(
            regulation_id="GDPR-2026-003",
            impact_mappings=[
                ImpactMapping(
                    requirement_id="REQ-1",
                    company_process="Deletion",
                    sop_document="SOP-UD-001",
                    current_practice="60-day SLA",
                    alignment_score=0.2,
                    notes="Major gap",
                )
            ],
            overall_impact="Critical",
        )
        assert assessment.regulation_id == "GDPR-2026-003"
        assert len(assessment.impact_mappings) == 1
        assert assessment.overall_impact == "Critical"

    def test_assessment_serialization(self):
        assessment = ImpactAssessment(
            regulation_id="GDPR-2026-003",
            impact_mappings=[],
            overall_impact="High",
        )
        data = json.loads(assessment.model_dump_json())
        assert data["regulation_id"] == "GDPR-2026-003"
        assert data["overall_impact"] == "High"
        assert data["impact_mappings"] == []

    def test_overall_impact_values(self):
        for level in ["Low", "Medium", "High", "Critical"]:
            assessment = ImpactAssessment(
                regulation_id="TEST",
                impact_mappings=[],
                overall_impact=level,
            )
            assert assessment.overall_impact == level


class TestImpactMapperPrompt:
    def test_prompt_mentions_gap_analyst(self):
        from agents.impact_mapper.prompts import IMPACT_MAPPER_SYSTEM_PROMPT

        assert "Gap Analyst" in IMPACT_MAPPER_SYSTEM_PROMPT

    def test_prompt_mentions_json_schema(self):
        from agents.impact_mapper.prompts import IMPACT_MAPPER_SYSTEM_PROMPT

        assert "requirement_id" in IMPACT_MAPPER_SYSTEM_PROMPT
        assert "company_process" in IMPACT_MAPPER_SYSTEM_PROMPT
        assert "sop_document" in IMPACT_MAPPER_SYSTEM_PROMPT
        assert "current_practice" in IMPACT_MAPPER_SYSTEM_PROMPT
        assert "alignment_score" in IMPACT_MAPPER_SYSTEM_PROMPT
        assert "overall_impact" in IMPACT_MAPPER_SYSTEM_PROMPT

    def test_prompt_mentions_alignment_score_range(self):
        from agents.impact_mapper.prompts import IMPACT_MAPPER_SYSTEM_PROMPT

        assert "0.0" in IMPACT_MAPPER_SYSTEM_PROMPT
        assert "1.0" in IMPACT_MAPPER_SYSTEM_PROMPT

    def test_prompt_mentions_severity_levels(self):
        from agents.impact_mapper.prompts import IMPACT_MAPPER_SYSTEM_PROMPT

        for level in ["Low", "Medium", "High", "Critical"]:
            assert level in IMPACT_MAPPER_SYSTEM_PROMPT

    def test_cascade_prompt_exists(self):
        from agents.impact_mapper.prompts import IMPACT_MAPPER_CASCADE_PROMPT

        assert (
            "Gap Analyst" in IMPACT_MAPPER_CASCADE_PROMPT
            or "gap" in IMPACT_MAPPER_CASCADE_PROMPT.lower()
        )


class TestExtractJsonBlock:
    def test_extracts_json_from_markdown(self):
        from agents.impact_mapper.agent import _extract_json_block

        text = 'Here is the result:\n```json\n{"key": "value"}\n```\nDone.'
        assert _extract_json_block(text) == '{"key": "value"}'

    def test_returns_full_text_when_no_json_block(self):
        from agents.impact_mapper.agent import _extract_json_block

        text = "Just plain text, no JSON here."
        assert _extract_json_block(text) == text

    def test_extracts_multiline_json(self):
        from agents.impact_mapper.agent import _extract_json_block

        json_content = '{\n  "regulation_id": "GDPR-2026-003",\n  "impact_mappings": []\n}'
        text = f"Result:\n```json\n{json_content}\n```"
        assert _extract_json_block(text) == json_content
