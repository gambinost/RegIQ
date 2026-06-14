# SOP-AC-001: Access Control & Role-Based Access

**Document ID:** SOP-AC-001
**Version:** 1.8
**Effective Date:** February 10, 2025
**Owner:** Engineering Team
**Review Cycle:** Semi-Annual

## 1. Purpose

This SOP defines the access control model and role-based permissions for all internal systems.

## 2. Role Definitions

| Role | Permissions | Scope |
|------|-------------|-------|
| Admin | Full CRUD + user management + system configuration | All systems |
| Data Owner | Read + Write for owned data, Read-only for others | Department data |
| Viewer | Read-only | Assigned modules only |

## 3. Access Provisioning

- New employee access is provisioned by the hiring manager via IT self-service portal
- Role assignment requires manager approval
- Access is granted per system (Nimbus CRM, Data Warehouse, Zendesk, HubSpot, Workday)
- Each system has its own access control list (ACL) managed independently by the department that owns it

## 4. Access Revocation

- Revocation triggered by: termination, role change, or manager request
- Revocation is performed manually by IT Operations for each system
- Average revocation time: 48 hours across all systems
- No centralized, automated revocation tool exists
- Cross-system revocation requires separate tickets per system

## 5. Audit Logging

- User login/logout events are logged in CloudWatch (90-day retention, see SOP-DR-001)
- Data modification events are logged per system with inconsistent schemas
- No centralized audit trail exists across all 5 systems
- Weekly access review reports are generated manually by IT Operations

## 6. Known Gaps for Data Erasure

- Decentralized access control means revoking a deleted user's access requires tickets to 5 separate system owners
- No single API or tool can revoke access across all systems simultaneously
- Audit logs of data access are not linked to erasure request workflows
- No automated mechanism to confirm that a deleted user's access has been fully revoked across all systems