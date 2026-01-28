---
id: TASK-100
title: Analyze partner data sharing and third-party model privacy implications
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - privacy
  - third-party
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how privacy mode interacts with partner data sharing (partnerDataShare flag) and third-party model providers. Document what data is shared with model providers when using non-Anthropic models and how privacy mode affects this.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary of Analysis

Investigated how privacy mode interacts with partner data sharing and third-party model providers in Cursor IDE 2.3.41.

### Key Findings

1. **partnerDataShare Flag**: A server-controlled boolean flag (`cursorai/donotchange/partnerDataShare`) that operates **independently** of privacy mode. When enabled, prompts and limited telemetry may be shared with model providers.

2. **Privacy Mode Discrepancy**: The UI claims "none of your questions or code will ever be stored...by any third-party" when Privacy Mode is enabled, but:
   - When using BYOK, requests go directly to third-party APIs
   - When explicitly selecting third-party models, data is sent to those providers
   - Third-party providers have their own retention policies outside Cursor's control

3. **Model Provider Routing**: Functions `l7r()` and `c7r()` detect model providers:
   - Claude models: `claude-*` prefix -> Anthropic
   - Gemini models: `gemini-*` prefix -> Google
   - GPT/O-series: -> OpenAI
   - Bedrock models: `us.anthropic.*` -> AWS

4. **BYOK System**: Allows direct API key usage for OpenAI, Claude, Google, and AWS Bedrock, meaning requests bypass Cursor servers entirely for billing purposes.

5. **Data Sharing Discount**: Field `data_sharing_discount_eligible` suggests pricing incentives for enabling data sharing.

6. **Grace Period**: One-day protection period for new users before data sharing activates.

### Files Changed
- Created `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-100-partner-data.md`

### Related Tasks
- TASK-76: Privacy Mode System
- TASK-78: AWS Bedrock Integration
<!-- SECTION:FINAL_SUMMARY:END -->
