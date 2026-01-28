---
id: TASK-78
title: Document AWS Bedrock IAM role authentication for Enterprise Cursor
status: Done
assignee: []
created_date: '2026-01-27 14:51'
updated_date: '2026-01-28 07:29'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Document AWS Bedrock IAM role authentication flow for Enterprise Cursor. Analyze how enterprise teams can configure IAM roles for Bedrock access, including the STS AssumeRole patterns, credential handling, and the "iam" sentinel value mechanism.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document BedrockState protobuf schema
- [x] #2 Document Team bedrock_iam_role and bedrock_external_id fields
- [x] #3 Document credential conversion flow
- [x] #4 Document IAM role validation API
- [x] #5 Document enterprise admin controls (BYOK disabled)
- [x] #6 Document supported Bedrock models and regional prefixes
- [x] #7 Document AWS IAM requirements for cross-account access
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Documented AWS Bedrock IAM role authentication for Enterprise Cursor in comprehensive analysis.

Key findings:
- Two authentication modes: user-provided credentials and enterprise IAM role assumption
- IAM role mode uses "iam" sentinel values for accessKey/secretKey
- Server performs STS AssumeRole with team's bedrockIamRole and bedrockExternalId
- Regional model prefix mapping: us.*, apac.*, eu.*, ca.*
- Enterprise admins can disable BYOK to force team-managed access
- ValidateBedrockIamRole RPC allows testing configuration before deployment

Output: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-78-bedrock-iam.md
<!-- SECTION:FINAL_SUMMARY:END -->
