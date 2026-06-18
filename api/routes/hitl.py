from fastapi import APIRouter
from pydantic import BaseModel

from models.report import ComplianceReport, RemediationTicket

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])

_hitl_decisions: dict[str, str] = {}
_generated_reports: dict[str, ComplianceReport] = {}
_latest_report_id: str | None = None

_mock_report = ComplianceReport(
    regulation_id="GDPR-2026-003",
    regulation_name="EU General Data Protection Regulation Amendment 2026",
    executive_summary="This regulation introduces stricter requirements for data retention and user deletion rights. Companies must now delete user data within 30 days of request, down from the previous 90-day window. Additionally, explicit consent must be renewed annually, and data portability must include AI training data. Failure to comply by September 1, 2026, carries penalties of up to 4% of global annual revenue.",
    generated_at="2026-06-15T10:30:00Z",
    compliance_deadline="2026-09-01",
    weeks_to_deadline=11.0,
    critical_path_weeks=9.0,
    total_gaps=7,
    critical_gaps=4,
    status="pending_approval",
    sequencing_note="FLAG-003 legal review is the foundational gate — REQ-005 and REQ-006 cannot proceed until legal sign-off is obtained. REQ-004 data inventory must complete before REQ-003 automation can be designed, and REQ-003 must precede REQ-001 erasure implementation. REQ-002 validation SOP is a parallel prerequisite for REQ-001.",
    tickets=[
        RemediationTicket(
            ticket_id="REM-GDPR-2026-003-01",
            title="Obtain legal review for 30-day erasure mandate interpretation",
            gap_ref="FLAG-003",
            priority="P0",
            owner_team="Legal & Compliance",
            effort_weeks=1.0,
            depends_on=[],
            actions=[
                "Brief external counsel on Article 17 amendment text and recitals",
                "Document legal interpretation of 'without undue delay' = 30 calendar days",
                "Obtain written legal opinion on scope exceptions and exemptions",
                "Distribute legal sign-off memo to Engineering and Compliance teams",
            ],
            done_criteria="Written legal opinion is approved and distributed to all teams implementing erasure changes",
        ),
        RemediationTicket(
            ticket_id="REM-GDPR-2026-003-02",
            title="Build cross-system data inventory for erasure pipeline",
            gap_ref="REQ-004",
            priority="P0",
            owner_team="Data Platform",
            effort_weeks=2.0,
            depends_on=[],
            actions=[
                "Catalog all systems storing PII (databases, caches, backups, analytics)",
                "Map data flow between systems to identify propagation paths",
                "Document retention policies per system and data category",
                "Create automated inventory sync job with schema change detection",
            ],
            done_criteria="Complete inventory of all PII-holding systems with verified data flow maps published to Confluence",
        ),
        RemediationTicket(
            ticket_id="REM-GDPR-2026-003-03",
            title="Deploy immutable audit logging infrastructure",
            gap_ref="REQ-006",
            priority="P0",
            owner_team="Platform Engineering",
            effort_weeks=2.0,
            depends_on=["REM-GDPR-2026-003-01"],
            actions=[
                "Provision append-only log storage with tamper-evident hashing",
                "Instrument erasure request receipt and completion timestamps",
                "Build audit log query API for supervisory authority access",
                "Implement 3-year retention policy with automated archival",
            ],
            done_criteria="Immutable audit logs capture all erasure events with timestamps and are queryable via API for 3 years minimum",
        ),
        RemediationTicket(
            ticket_id="REM-GDPR-2026-003-04",
            title="Update consent validation SOP with annual renewal requirement",
            gap_ref="REQ-002",
            priority="P1",
            owner_team="Growth & Compliance",
            effort_weeks=2.0,
            depends_on=[],
            actions=[
                "Rewrite SOP-UD-002 to include 12-month renewal cycle",
                "Design consent renewal email template with opt-out link",
                "Build grace-period handling logic (30-day post-expiry window)",
                "Train customer support on new consent verification procedure",
            ],
            done_criteria="Updated SOP-UD-002 is approved and consent renewal emails are configured in the CRM with grace-period logic tested",
        ),
        RemediationTicket(
            ticket_id="REM-GDPR-2026-003-05",
            title="Implement automated cross-system erasure workflow",
            gap_ref="REQ-003",
            priority="P0",
            owner_team="Platform Engineering",
            effort_weeks=3.0,
            depends_on=["REM-GDPR-2026-003-02"],
            actions=[
                "Design orchestrated erasure DAG based on data inventory maps",
                "Build idempotent deletion adapters for each PII system",
                "Implement progress tracking and retry logic for partial failures",
                "Add completion verification step that confirms zero remaining PII references",
                "Integrate with audit logging infrastructure from REM-03",
            ],
            done_criteria="End-to-end automated erasure pipeline deletes all PII across all systems within 30 days and logs each step to audit infrastructure",
        ),
        RemediationTicket(
            ticket_id="REM-GDPR-2026-003-06",
            title="Implement breach notification escalation within 72 hours",
            gap_ref="REQ-005",
            priority="P0",
            owner_team="Security Operations",
            effort_weeks=1.5,
            depends_on=["REM-GDPR-2026-003-01", "REM-GDPR-2026-003-03"],
            actions=[
                "Update incident response runbook with 72-hour escalation timeline",
                "Configure PagerDuty automation for immediate breach detection alerts",
                "Build DPA notification template pre-filled with audit log references",
                "Run tabletop exercise with Security, Legal, and Comms teams",
            ],
            done_criteria="Incident response runbook specifies 72-hour DPA notification and automated alerting is tested via tabletop exercise",
        ),
        RemediationTicket(
            ticket_id="REM-GDPR-2026-003-07",
            title="Reduce data deletion SLA from 60 days to 30 days",
            gap_ref="REQ-001",
            priority="P0",
            owner_team="Platform Engineering",
            effort_weeks=3.0,
            depends_on=["REM-GDPR-2026-003-04", "REM-GDPR-2026-003-05"],
            actions=[
                "Retune batch deletion scheduler from 60-day to 30-day SLA window",
                "Optimize long-running deletion queries for parallel execution",
                "Add real-time SLA countdown dashboard for compliance monitoring",
                "Conduct load test with 10x peak erasure request volume",
            ],
            done_criteria="Data deletion completes within 30 calendar days for all erasure requests, verified by load test at 10x peak volume",
        ),
    ],
)


class DecisionRequest(BaseModel):
    decision: str
    reason: str | None = None


class DecisionResponse(BaseModel):
    status: str
    decision: str


@router.post("/report/{regulation_id}")
async def store_hitl_report(regulation_id: str, report: ComplianceReport):
    """Store a real generated report from the Remediation Planner agent."""
    global _latest_report_id
    _generated_reports[regulation_id] = report
    _latest_report_id = regulation_id
    return {"status": "stored", "regulation_id": regulation_id}


@router.get("/report/{regulation_id}", response_model=ComplianceReport)
async def get_hitl_report(regulation_id: str):
    """Return a generated report if available, otherwise fall back to mock."""
    if regulation_id in _generated_reports:
        return _generated_reports[regulation_id]
    return _mock_report


@router.get("/latest", response_model=ComplianceReport)
async def get_latest_report():
    """Return the most recently generated report, or mock if none."""
    if _latest_report_id and _latest_report_id in _generated_reports:
        return _generated_reports[_latest_report_id]
    return _mock_report


@router.post("/respond", response_model=DecisionResponse)
async def submit_hitl_decision(request: DecisionRequest):
    decision = request.decision.upper()
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError("Decision must be APPROVED or REJECTED")

    _hitl_decisions["GDPR-2026-003"] = decision
    return DecisionResponse(status="received", decision=decision)


@router.get("/status/{regulation_id}")
async def get_hitl_status(regulation_id: str):
    decision = _hitl_decisions.get(regulation_id)
    if not decision:
        return {"status": "pending", "decision": None}
    return {"status": "completed", "decision": decision}
