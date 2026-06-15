from fastapi import APIRouter
from pydantic import BaseModel

from models.report import ComplianceReport, RemediationTicket

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])

# In-memory store for demo (matches PRD: "In-memory dict in FastAPI is fine for demo")
_hitl_decisions: dict[str, str] = {}

# Pre-seed mock report for frontend development
_mock_report = ComplianceReport(
    regulation_id="REG-2024-001",
    regulation_name="EU General Data Protection Regulation Amendment 2026",
    executive_summary="This regulation introduces stricter requirements for data retention and user deletion rights. Companies must now delete user data within 30 days of request, down from the previous 90-day window. Additionally, explicit consent must be renewed annually, and data portability must include AI training data. Failure to comply by September 1, 2026, carries penalties of up to 4% of global annual revenue.",
    total_gaps=7,
    critical_gaps=2,
    status="pending_approval",
    tickets=[
        RemediationTicket(
            ticket_id="TICK-001",
            gap_id="GAP-001",
            title="Reduce data deletion SLA from 60 days to 30 days",
            description="Current SOP allows 60 days for full user deletion. The new regulation mandates 30 days. This requires updating the user deletion workflow, retraining customer support, and modifying automated scripts.",
            priority="Critical",
            owner="Platform Engineering",
            estimated_effort_days=14.0,
            deadline="2026-08-15",
        ),
        RemediationTicket(
            ticket_id="TICK-002",
            gap_id="GAP-002",
            title="Implement annual consent renewal emails",
            description="Currently, user consent is collected once at signup. The amendment requires explicit renewal every 12 months. Need to build a consent management system with automated reminders and grace-period handling.",
            priority="Critical",
            owner="Growth & Compliance",
            estimated_effort_days=21.0,
            deadline="2026-07-20",
        ),
        RemediationTicket(
            ticket_id="TICK-003",
            gap_id="GAP-003",
            title="Add AI training data to data portability exports",
            description="Data portability requests currently include structured user profile data only. The amendment includes 'data used to train algorithms or AI models.' Need to identify and export model-training datasets.",
            priority="High",
            owner="ML Platform",
            estimated_effort_days=10.0,
            deadline="2026-08-01",
        ),
        RemediationTicket(
            ticket_id="TICK-004",
            gap_id="GAP-004",
            title="Update privacy policy and legal documents",
            description="Privacy policy, terms of service, and cookie policy must be updated to reflect the new retention periods and consent renewal requirements.",
            priority="Medium",
            owner="Legal",
            estimated_effort_days=3.0,
            deadline="2026-07-01",
        ),
        RemediationTicket(
            ticket_id="TICK-005",
            gap_id="GAP-005",
            title="Implement breach notification escalation within 72 hours",
            description="Current breach notification protocol requires 5 business days. New regulation requires 72 hours. Update incident response runbook and pager automation.",
            priority="Medium",
            owner="Security",
            estimated_effort_days=5.0,
            deadline="2026-08-10",
        ),
    ],
)


class DecisionRequest(BaseModel):
    decision: str  # "APPROVED" or "REJECTED"
    reason: str | None = None


class DecisionResponse(BaseModel):
    status: str
    decision: str


@router.get("/report/{regulation_id}", response_model=ComplianceReport)
async def get_hitl_report(regulation_id: str):
    """Return the current ComplianceReport for HITL review."""
    # For demo, return the seeded mock report regardless of ID
    return _mock_report


@router.post("/respond", response_model=DecisionResponse)
async def submit_hitl_decision(request: DecisionRequest):
    """Accept human decision from HITL review UI."""
    decision = request.decision.upper()
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError("Decision must be APPROVED or REJECTED")

    _hitl_decisions["REG-2024-001"] = decision
    return DecisionResponse(status="received", decision=decision)


@router.get("/status/{regulation_id}")
async def get_hitl_status(regulation_id: str):
    """Return the current decision status for a regulation."""
    decision = _hitl_decisions.get(regulation_id)
    if not decision:
        return {"status": "pending", "decision": None}
    return {"status": "completed", "decision": decision}
