---
id: TASK-91
title: Investigate enterprise admin Bedrock access controls
status: Done
assignee: []
created_date: '2026-01-27 22:35'
updated_date: '2026-01-28 06:41'
labels:
  - aws
  - bedrock
  - enterprise
  - admin
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Questions to answer:
1. Can enterprise admins restrict which Bedrock models team members can use?
2. Is there per-user or per-team rate limiting for Bedrock API calls?
3. How does Bedrock usage integrate with Cursor's usage analytics?
4. Are there audit logs for Bedrock requests showing which user made which request?

Related to admin settings and team configuration.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Completed analysis of enterprise Bedrock access controls in Cursor IDE 2.3.41

Key findings: Enterprise IAM role-based access, team-level configuration, general model blocking (not Bedrock-specific)

No evidence of Bedrock-specific rate limiting or audit logging in client code - likely server-side

Analysis written to: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-91-enterprise-bedrock.md
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Investigated enterprise admin Bedrock access controls in Cursor IDE 2.3.41.\n\nKey discoveries:\n1. Enterprise IAM Role-Based Access: Teams can configure IAM roles with external IDs for cross-account Bedrock access without individual credentials\n2. Team Settings: bedrockIamRole and bedrockExternalId fields on Team object\n3. Validation API: ValidateBedrockIamRole and DeleteBedrockIamRole gRPC methods\n4. Supported Models: 7 hardcoded Claude models with regional prefixes (us/apac/eu/ca)\n5. General Model Controls: allowedModels/blockedModels in team admin settings apply to ALL models, not Bedrock-specific\n6. BYOK Enforcement: Enterprise can disable bring-your-own-key to force company-managed API access\n\nLimitations found:\n- No Bedrock-specific model restrictions (only general model blocking)\n- No client-side rate limiting for Bedrock (likely server-side)\n- No audit logging in client code (would be server-side)\n\nAnalysis document: reveng_2.3.41/analysis/TASK-91-enterprise-bedrock.md
<!-- SECTION:FINAL_SUMMARY:END -->
