---
id: DRAFT-1
title: Investigate Bedrock server-side STS AssumeRole implementation
status: Draft
assignee: []
created_date: '2026-01-28 07:30'
labels:
  - bedrock
  - enterprise
  - server-side
  - follow-up
dependencies:
  - TASK-78
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up from TASK-78. The client sends "iam" sentinel values for credentials, and the server performs STS AssumeRole. Key questions to answer if server code becomes available:

1. How does the server detect the "iam" sentinel and route to IAM role authentication?
2. What is the TTL for cached temporary credentials?
3. Does the server cache assumed role credentials across requests?
4. How are Bedrock API errors (rate limits, access denied) handled and reported to clients?
5. Is there audit logging for which user made which Bedrock request?

This investigation requires access to server-side code (aiserver backend) which may not be available through client decompilation.
<!-- SECTION:DESCRIPTION:END -->
