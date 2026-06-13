import json

from models.requirement import ComplianceRequirement, ParsedRequirements


SAMPLE_PARSED = ParsedRequirements(
    regulation_id="GDPR-2026-003",
    requirements=[
        ComplianceRequirement(
            requirement_id="REQ-GDPR-2026-003-1",
            source_article="Article 17(1)",
            obligation="Erase personal data within 30 calendar days of receiving a valid erasure request",
            deadline="30 calendar days",
            affected_entities=["data controllers", "data processors"],
            severity="Critical",
        ),
        ComplianceRequirement(
            requirement_id="REQ-GDPR-2026-003-2",
            source_article="Article 17(2)",
            obligation="Implement automated erasure workflows capable of cross-system deletion within the 30-day window",
            deadline="2026-09-01",
            affected_entities=["data controllers"],
            severity="High",
        ),
        ComplianceRequirement(
            requirement_id="REQ-GDPR-2026-003-3",
            source_article="Article 17(3)",
            obligation="Maintain immutable audit logs of all erasure operations for a minimum of 3 years",
            deadline="3 years retention",
            affected_entities=["data controllers", "supervisory authorities"],
            severity="High",
        ),
    ],
    total_count=3,
)


class TestComplianceRequirementModel:
    def test_requirement_creation(self):
        r = SAMPLE_PARSED.requirements[0]
        assert r.requirement_id == "REQ-GDPR-2026-003-1"
        assert r.severity == "Critical"
        assert "data controllers" in r.affected_entities

    def test_requirement_serialization(self):
        json_str = SAMPLE_PARSED.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["regulation_id"] == "GDPR-2026-003"
        assert len(parsed["requirements"]) == 3
        assert parsed["total_count"] == 3

    def test_requirement_defaults(self):
        r = ComplianceRequirement(
            requirement_id="REQ-001",
            source_article="Art. 1",
            obligation="Do something",
            severity="Low",
        )
        assert r.deadline is None
        assert r.affected_entities == []

    def test_requirement_round_trip(self):
        json_str = SAMPLE_PARSED.model_dump_json()
        restored = ParsedRequirements.model_validate_json(json_str)
        assert restored.regulation_id == SAMPLE_PARSED.regulation_id
        assert len(restored.requirements) == 3
        assert restored.total_count == 3

    def test_each_severity_level(self):
        for level in ["Critical", "High", "Medium", "Low"]:
            r = ComplianceRequirement(
                requirement_id="REQ-TEST",
                source_article="Art. 1",
                obligation="Test",
                severity=level,
            )
            assert r.severity == level


class TestParsedRequirementsModel:
    def test_total_count_matches_requirements(self):
        assert SAMPLE_PARSED.total_count == len(SAMPLE_PARSED.requirements)

    def test_empty_requirements(self):
        parsed = ParsedRequirements(
            regulation_id="EMPTY-001",
            requirements=[],
            total_count=0,
        )
        assert len(parsed.requirements) == 0
        assert parsed.total_count == 0


class TestLegalParserSystemPrompt:
    def test_prompt_mentions_impact_mapper(self):
        from agents.legal_parser.prompts import LEGAL_PARSER_SYSTEM_PROMPT

        assert "Impact Mapper" in LEGAL_PARSER_SYSTEM_PROMPT

    def test_prompt_mentions_severity_levels(self):
        from agents.legal_parser.prompts import LEGAL_PARSER_SYSTEM_PROMPT

        for level in ["Critical", "High", "Medium", "Low"]:
            assert level in LEGAL_PARSER_SYSTEM_PROMPT

    def test_prompt_asks_for_structured_output(self):
        from agents.legal_parser.prompts import LEGAL_PARSER_SYSTEM_PROMPT

        assert "json" in LEGAL_PARSER_SYSTEM_PROMPT.lower()
        assert "requirement_id" in LEGAL_PARSER_SYSTEM_PROMPT

    def test_prompt_asks_for_source_article(self):
        from agents.legal_parser.prompts import LEGAL_PARSER_SYSTEM_PROMPT

        assert "source" in LEGAL_PARSER_SYSTEM_PROMPT.lower()
        assert "obligation" in LEGAL_PARSER_SYSTEM_PROMPT.lower()

    def test_prompt_mentions_impact_mapper_forwarding(self):
        from agents.legal_parser.prompts import LEGAL_PARSER_SYSTEM_PROMPT

        assert "forwarded to the Impact Mapper" in LEGAL_PARSER_SYSTEM_PROMPT
