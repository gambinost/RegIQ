from pydantic import BaseModel, Field


class ImpactMapping(BaseModel):
    requirement_id: str
    company_process: str
    sop_document: str
    current_practice: str
    alignment_score: float = Field(ge=0.0, le=1.0)
    notes: str = ""


class ImpactAssessment(BaseModel):
    regulation_id: str
    impact_mappings: list[ImpactMapping]
    overall_impact: str = Field(description="One of: Low, Medium, High, Critical")
