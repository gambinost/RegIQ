from pydantic import BaseModel, Field


class RegulationInput(BaseModel):
    regulation_id: str
    title: str
    source: str
    jurisdiction: str
    effective_date: str
    industry_tags: list[str] = Field(default_factory=list)
    summary: str
    full_text: str


class RegulationAssessment(BaseModel):
    regulation_id: str
    regulation_name: str
    jurisdiction: str
    effective_date: str | None = None
    urgency: str = Field(description="One of: Low, Medium, High, Critical")
    urgency_reasoning: str
    key_requirements: list[str] = Field(default_factory=list)
    summary: str
