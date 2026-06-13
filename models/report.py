from pydantic import BaseModel, Field


class RemediationTicket(BaseModel):
    ticket_id: str
    gap_id: str
    title: str
    description: str
    priority: str = Field(description="One of: Low, Medium, High, Critical")
    owner: str = ""
    estimated_effort_days: float = 0.0
    deadline: str = ""


class ComplianceReport(BaseModel):
    regulation_id: str
    regulation_name: str
    executive_summary: str
    total_gaps: int
    critical_gaps: int
    tickets: list[RemediationTicket]
    status: str = "pending_approval"
