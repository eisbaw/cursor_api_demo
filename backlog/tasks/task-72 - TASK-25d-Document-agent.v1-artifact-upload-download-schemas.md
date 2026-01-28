---
id: TASK-72
title: 'TASK-25d: Document agent.v1 artifact upload/download schemas'
status: Done
assignee: []
created_date: '2026-01-27 14:50'
updated_date: '2026-01-28 07:22'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Document the agent.v1 artifact upload/download schemas found in Cursor IDE 2.3.41.

Analysis completed covering:
- agent.v1.ControlService artifact methods (ListArtifacts, UploadArtifacts)
- ArtifactUploadStatus and ArtifactUploadDispatchStatus enums
- ArtifactUploadMetadata with progress tracking fields
- ArtifactUploadInstruction with presigned URL support
- aiserver.v1.BackgroundComposerService artifact methods
- Slack integration for artifact sharing
- anyrun.v1 presigned URL and blob storage format
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document agent.v1 artifact upload schemas
- [x] #2 Document artifact download mechanisms
- [x] #3 Identify presigned URL handling patterns
- [x] #4 Document Slack integration fields
- [x] #5 Include reconstructed protobuf definitions
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Documented the complete artifact upload/download schema architecture in Cursor IDE 2.3.41.

## Key Findings

### agent.v1.ControlService Artifact Methods
- `ListArtifacts`: Query current artifact metadata and upload status
- `UploadArtifacts`: Request upload instructions with presigned URLs

### Artifact Upload Schema
- `ArtifactUploadMetadata`: Tracks file path, size, status, bytes uploaded, error messages, attempt counts, and timestamps
- `ArtifactUploadInstruction`: Contains presigned upload URL, HTTP method, headers, content type, and optional Slack URLs
- Upload status enum: UNSPECIFIED, NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED
- Dispatch status enum: UNSPECIFIED, ACCEPTED, REJECTED, SKIPPED_ALREADY_IN_PROGRESS

### aiserver.v1.BackgroundComposerService
- `ListBackgroundComposerArtifacts`: List artifacts for a cloud agent session
- `GetBackgroundComposerArtifact`: Get presigned download URL
- `GetBackgroundComposerArtifactBytes`: Get artifact content directly
- `StreamBackgroundComposerArtifact`: Stream large artifacts in chunks

### Additional Findings
- Slack integration fields for sharing artifacts to Slack channels
- BlobStorageFormat enum (LEGACY_UNSPECIFIED, V1) with feature gate control
- Presigned URL pattern used for both upload and download operations

## Output
Analysis written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-72-artifact-schemas.md`
<!-- SECTION:FINAL_SUMMARY:END -->
