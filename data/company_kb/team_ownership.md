# Team Ownership & System Mapping

**Document ID:** REF-TEAM-001
**Version:** 1.0
**Effective Date:** January 1, 2025
**Owner:** CTO Office

## System Ownership

| System | Primary Team | Secondary Team | Platform |
|--------|-------------|---------------|----------|
| Nimbus CRM | Security Team | IT Operations | AWS (us-east-1) |
| Data Warehouse | Data Engineering | IT Operations | Snowflake |
| Zendesk (Support) | Customer Success | IT Operations | SaaS |
| HubSpot (Marketing) | Marketing | Data Engineering | SaaS |
| Workday (HR) | People Operations | IT Operations | SaaS |
| CloudWatch Logs | Engineering | Security Team | AWS |
| S3 Archive | Data Engineering | Security Team | AWS |

## Responsibility Matrix (RACI)

### Erasure Request Handling

| Step | Security | IT Ops | Legal | Compliance | Data Eng |
|------|----------|--------|-------|------------|----------|
| Request intake | C | I | I | A | I |
| Identity verification | R | I | I | A | I |
| Legal hold check | I | I | R | A | I |
| Cross-system deletion | C | R | I | A | C |
| Audit logging | R | C | I | A | I |
| Confirmation to user | C | R | I | A | I |

### New Regulation Assessment

| Step | Security | IT Ops | Legal | Compliance | Data Eng |
|------|----------|--------|-------|------------|----------|
| Impact analysis | C | C | R | A | C |
| Gap identification | C | I | C | R | I |
| Remediation planning | C | R | C | A | R |
| Implementation | C | R | I | A | R |
| Testing & validation | R | R | I | A | C |

## Key Contacts

| Team | Lead | Email | Escalation |
|------|------|-------|------------|
| Security Team | Ahmed K. | security@company.com | CISO |
| IT Operations | Maria L. | itops@company.com | VP Engineering |
| Legal | David R. | legal@company.com | General Counsel |
| Compliance | Sarah T. | compliance@company.com | DPO |
| Data Engineering | Wei Z. | dataeng@company.com | VP Engineering |