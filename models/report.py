from pydantic import BaseModel


class RemediationTicket(BaseModel):
    ticket_id: str
    title: str
    gap_ref: str
    priority: str
    owner_team: str
    effort_weeks: float
    depends_on: list[str]
    actions: list[str]
    done_criteria: str


class ComplianceReport(BaseModel):
    regulation_id: str
    regulation_name: str
    executive_summary: str
    generated_at: str
    compliance_deadline: str
    weeks_to_deadline: float
    critical_path_weeks: float
    tickets: list[RemediationTicket]
    sequencing_note: str
    total_gaps: int = 0
    critical_gaps: int = 0
    status: str = "pending_approval"
    timing: dict | None = None
