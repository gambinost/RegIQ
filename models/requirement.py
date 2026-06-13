from pydantic import BaseModel, Field


class ComplianceRequirement(BaseModel):
    requirement_id: str
    source_article: str
    obligation: str
    deadline: str | None = None
    affected_entities: list[str] = Field(default_factory=list)
    severity: str = Field(description="One of: Low, Medium, High, Critical")


class ParsedRequirements(BaseModel):
    regulation_id: str
    requirements: list[ComplianceRequirement]
    total_count: int
