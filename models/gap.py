from pydantic import BaseModel, Field


class ComplianceGap(BaseModel):
    requirement_id: str
    obligation: str
    current_practice: str
    gap_description: str
    severity: str = Field(description="One of: Low, Medium, High, Critical")
    affected_systems: list[str] = Field(default_factory=list)


class GapAnalysis(BaseModel):
    regulation_id: str
    gaps: list[ComplianceGap]
    total_gaps: int
    critical_count: int
