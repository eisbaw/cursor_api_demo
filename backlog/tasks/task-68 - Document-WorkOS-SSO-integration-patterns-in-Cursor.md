---
id: TASK-68
title: Document WorkOS SSO integration patterns in Cursor
status: Done
assignee: []
created_date: '2026-01-27 14:50'
updated_date: '2026-01-28 00:13'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed analysis of WorkOS/SSO patterns in Cursor IDE v2.3.41.

Key findings:
1. WorkOS is NOT directly used for SSO - the reference found was only a copyright notice for Radix UI Primitives library
2. Cursor uses its own proprietary OAuth 2.0 + PKCE authentication system with prod.authentication.cursor.sh as the auth domain
3. Enterprise SSO is handled through team-based authentication via /auth/poll endpoint and team membership detection
4. Documented the complete authentication flow including PKCE challenge, token polling, and token storage
5. Mapped enterprise features: membership types (FREE/PRO/PRO_PLUS/ENTERPRISE/FREE_TRIAL/ULTRA), team roles, admin settings, and privacy mode enforcement
6. Identified AWS Bedrock integration for enterprise private AI deployment

Created 3 follow-up tasks:
- TASK-151: Investigate Cursor's custom Auth0 tenant and OAuth flow
- TASK-152: Document enterprise team admin settings enforcement  
- TASK-153: Analyze Cursor's multi-provider authentication (GitHub, Google, SSO)
<!-- SECTION:FINAL_SUMMARY:END -->
