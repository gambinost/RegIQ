# SOP-UD-001: User Data Deletion

**Document ID:** SOP-UD-001
**Version:** 2.3
**Effective Date:** January 15, 2025
**Owner:** Security Team
**Review Cycle:** Annual

## 1. Purpose

This SOP defines the process for handling user data deletion requests in compliance with applicable data protection regulations.

## 2. Scope

All personal data processed through the Nimbus CRM platform, including user profiles, transaction history, support tickets, and associated metadata.

## 3. Current Deletion Process

### 3.1 Request Intake

- User submits deletion request via the Nimbus CRM self-service portal or by emailing privacy@company.com
- Request is logged as a Jira ticket in the PRIV project (ticket type: Data Deletion Request)
- Auto-acknowledgment email sent to user within 24 hours

### 3.2 Verification

- Privacy Team verifies identity of requestor (email match + security question)
- Cross-reference with active accounts in Nimbus CRM
- Verification must be completed within 5 business days

### 3.3 Approval Chain

The deletion request requires three approvals before execution:

1. **Privacy Team Lead** — Confirms request is valid and user identity verified
2. **Legal Counsel** — Confirms no legal hold or regulatory retention requirement
3. **IT Operations Manager** — Confirms technical feasibility and schedules execution

Each approver has up to 10 business days to review. Average total approval time: 20 business days.

### 3.4 Execution

- Approved requests are batched and processed on the 15th of each month
- Deletion is performed across all Nimbus CRM modules:
  - User profiles and preferences
  - Transaction history (all payment records older than 7 years are archived separately)
  - Support ticket history
  - Marketing engagement data
  - API access logs
- Manual confirmation email sent to requestor upon completion
- Total average processing time from request to completion: **60 calendar days**

### 3.5 Exceptions

- Data under legal hold is flagged but not deleted
- Archived payment records (7+ years old) require separate manual deletion from the legacy finance system
- Data shared with third-party partners requires individual notification (30-day notice period)

## 4. Known Gaps

- No automated cross-system deletion workflow exists
- Deletion relies on batch processing (monthly)
- Third-party data sharing requires manual notification per partner
- No real-time audit log of deletion operations (only monthly batch reports)

## 5. Responsible Teams

| Step | Team | Contact |
|------|------|---------|
| Request Intake | Privacy Team | privacy@company.com |
| Verification | Privacy Team | privacy@company.com |
| Legal Review | Legal | legal@company.com |
| Technical Review | IT Operations | itops@company.com |
| Execution | IT Operations | itops@company.com |