# SOP-DR-001: Data Retention Policy

**Document ID:** SOP-DR-001
**Version:** 3.1
**Effective Date:** March 1, 2025
**Owner:** Compliance Team
**Review Cycle:** Annual

## 1. Purpose

This policy defines retention periods and deletion procedures for all data categories processed by the organization.

## 2. Data Categories and Retention Periods

| Data Category | Retention Period | Storage Location |
|---------------|-----------------|------------------|
| Active user accounts | Duration of account + 3 years after closure | Nimbus CRM (PostgreSQL) |
| Transaction records | 7 years from transaction date | Nimbus CRM + Data Warehouse |
| Support tickets | 2 years after resolution | Zendesk |
| Marketing engagement | 1 year after last interaction | HubSpot |
| API access logs | 90 days | CloudWatch Logs |
| Audit trail logs | 5 years | S3 Archive |
| Employee records | Duration of employment + 7 years | Workday |
| Third-party shared data | Per contract terms (minimum 1 year) | Varies |

## 3. User Data Post-Closure

When a user account is closed (voluntary or involuntary):

- User profile and preferences: retained for **3 years** from account closure date
- Transaction history: retained for 7 years from last transaction
- Support ticket history: retained for 2 years from resolution
- Marketing data: purged within 30 days of closure notification

Data subject to legal hold is excluded from automatic purge schedules.

## 4. Deletion Procedures

- Monthly batch purge runs on the 1st of each month
- Deletion is soft-delete with 30-day recovery window, then hard-delete
- Hard deletion is irreversible and covers all replicas and backups within one additional backup cycle (30 days)
- Cross-system deletion relies on manual coordination between teams

## 5. Conflict with Right to Erasure

Current policy retains inactive user data for 3 years after account closure. Under GDPR Article 17, data subjects may request erasure at any time. The current retention schedule does not support erasure within 30 days because:

- Data is distributed across 5 systems (Nimbus CRM, PostgreSQL, Data Warehouse, Zendesk, HubSpot)
- No automated cross-system purge workflow exists
- Monthly batch processing means up to 31-day delay before next purge cycle
- Soft-delete recovery window adds another 30 days

## 6. Responsible Teams

| Area | Team |
|------|------|
| Policy & compliance | Compliance Team |
| Data warehouse operations | Data Engineering |
| CRM operations | IT Operations |
| Legal holds | Legal |