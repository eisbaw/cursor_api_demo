# TASK-72: agent.v1 Artifact Upload/Download Schemas

## Overview

This document analyzes the artifact upload and download mechanisms in Cursor IDE 2.3.41, focusing on the `agent.v1` protobuf schemas for file transfer operations between the local IDE and cloud agents.

## Key Findings

### 1. agent.v1.ControlService - Artifact Methods

The `agent.v1.ControlService` (line 807539) exposes two artifact-related RPC methods:

```
listArtifacts:
    name: "ListArtifacts"
    I: iLf (ListArtifactsRequest)
    O: sLf (ListArtifactsResponse)
    kind: Unary

uploadArtifacts:
    name: "UploadArtifacts"
    I: rLf (UploadArtifactsRequest)
    O: lLf (UploadArtifactsResponse)
    kind: Unary
```

Location: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js` lines 807601-807611

### 2. Artifact Upload Status Enum (agent.v1.ArtifactUploadStatus)

Lines 806441-806459 define upload status tracking:

| Enum Value | Name |
|------------|------|
| 0 | ARTIFACT_UPLOAD_STATUS_UNSPECIFIED |
| 1 | ARTIFACT_UPLOAD_STATUS_NOT_STARTED |
| 2 | ARTIFACT_UPLOAD_STATUS_IN_PROGRESS |
| 3 | ARTIFACT_UPLOAD_STATUS_COMPLETED |
| 4 | ARTIFACT_UPLOAD_STATUS_FAILED |

### 3. Artifact Upload Dispatch Status Enum (agent.v1.ArtifactUploadDispatchStatus)

Lines 806460-806475 define dispatch status:

| Enum Value | Name |
|------------|------|
| 0 | ARTIFACT_UPLOAD_DISPATCH_STATUS_UNSPECIFIED |
| 1 | ARTIFACT_UPLOAD_DISPATCH_STATUS_ACCEPTED |
| 2 | ARTIFACT_UPLOAD_DISPATCH_STATUS_REJECTED |
| 3 | ARTIFACT_UPLOAD_DISPATCH_STATUS_SKIPPED_ALREADY_IN_PROGRESS |

### 4. ListArtifactsRequest (agent.v1.ListArtifactsRequest)

Line 807171 - Empty request message (no fields required).

### 5. ArtifactUploadMetadata (agent.v1.ArtifactUploadMetadata)

Lines 807197-807250 define metadata for each artifact:

| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | absolute_path | string | Full path to the artifact file |
| 2 | size_bytes | uint64 | File size in bytes |
| 3 | updated_at_unix_ms | int64 | Last modification timestamp (Unix ms) |
| 4 | status | ArtifactUploadStatus | Current upload status |
| 5 | bytes_uploaded | uint64 | Progress - bytes transferred so far |
| 6 | last_error | string | Error message if upload failed |
| 7 | upload_attempts | uint32 | Number of upload attempts made |
| 8 | last_started_at_unix_ms | int64 | When the last upload attempt started |
| 9 | last_finished_at_unix_ms | int64 | When the last upload attempt finished |
| 10 | upload_id | string | Unique identifier for the upload operation |

### 6. ListArtifactsResponse (agent.v1.ListArtifactsResponse)

Lines 807273-807282 - Contains repeated artifacts field using ArtifactUploadMetadata.

### 7. UploadArtifactsRequest (agent.v1.UploadArtifactsRequest)

Lines 807305-807314:

| Field # | Name | Type |
|---------|------|------|
| 1 | uploads | repeated ArtifactUploadInstruction |

### 8. ArtifactUploadInstruction (agent.v1.ArtifactUploadInstruction)

Lines 807337-807382 - Core upload instructions with presigned URL support:

| Field # | Name | Type | Description |
|---------|------|------|-------------|
| 1 | absolute_path | string | Local file path to upload |
| 2 | upload_url | string | Presigned URL for upload (likely S3/GCS) |
| 3 | method | string | HTTP method (typically PUT) |
| 4 | headers | map<string,string> | HTTP headers for the upload request |
| 5 | content_type | string (optional) | MIME type of the artifact |
| 6 | slack_upload_url | string (optional) | Alternative URL for Slack integration |
| 7 | slack_file_id | string (optional) | Slack file ID for notifications |

### 9. ArtifactUploadDispatchResult (agent.v1.ArtifactUploadDispatchResult)

Lines 807405-807429 - Result for each upload dispatch:

| Field # | Name | Type |
|---------|------|------|
| 1 | absolute_path | string |
| 2 | status | ArtifactUploadDispatchStatus |
| 3 | message | string |
| 4 | slack_file_id | string (optional) |

### 10. UploadArtifactsResponse (agent.v1.UploadArtifactsResponse)

Lines 807452-807461:

| Field # | Name | Type |
|---------|------|------|
| 1 | results | repeated ArtifactUploadDispatchResult |

## Background Composer Artifact Schemas (aiserver.v1)

The aiserver.v1 package provides additional artifact handling for the Background Composer (cloud agent) feature.

### aiserver.v1.BackgroundComposerArtifact

Lines 341584-341608:

| Field # | Name | Type |
|---------|------|------|
| 1 | absolute_path | string |
| 2 | size_bytes | int64 |
| 3 | updated_at_unix_ms | int64 |

### aiserver.v1.ListBackgroundComposerArtifactsRequest

Line 341565 - Request with bc_id (background composer ID) field.

### aiserver.v1.ListBackgroundComposerArtifactsResponse

Line 341627 - Contains repeated artifacts array.

### aiserver.v1.GetBackgroundComposerArtifactRequest

Lines 341654-341665:

| Field # | Name | Type |
|---------|------|------|
| 1 | bc_id | string |
| 2 | absolute_path | string |

### aiserver.v1.GetBackgroundComposerArtifactResponse

Line 341684 - Returns URL for downloading the artifact (presigned URL).

### aiserver.v1.GetBackgroundComposerArtifactBytesRequest

Lines 341710-341721 - Same fields as GetBackgroundComposerArtifactRequest.

### aiserver.v1.GetBackgroundComposerArtifactBytesResponse

Lines 341741-341752:

| Field # | Name | Type |
|---------|------|------|
| 1 | content | bytes |
| 2 | content_type | string |

### aiserver.v1.StreamBackgroundComposerArtifactRequest

Lines 341828-341839 - Same fields as GetBackgroundComposerArtifactRequest.

### aiserver.v1.StreamBackgroundComposerArtifactResponse

Lines 341860-341876 - Streaming response for large artifacts:

| Field # | Name | Type |
|---------|------|------|
| 1 | content_chunk | bytes |
| 2 | content_type | string |
| 3 | total_size | int64 |

## Presigned URL Mechanism

### anyrun.v1.ExternalSnapshot

Lines 311237-311268 and 452627-452658 show presigned URL usage for snapshots:

| Field # | Name | Type |
|---------|------|------|
| 1 | snapshot_id | string |
| 2 | presigned_url | string |
| 3 | image_metadata | ImageMetadata |
| 4 | blob_storage_format | BlobStorageFormat |

### anyrun.v1.BlobStorageFormat

Lines 310547-310552:

| Enum Value | Name |
|------------|------|
| 0 | BLOB_STORAGE_FORMAT_LEGACY_UNSPECIFIED |
| 1 | BLOB_STORAGE_FORMAT_V1 |

Feature gate `cloud_agent_enable_blob_storage_format_v1` (line 294409) controls which format is used.

## BackgroundComposerService Artifact Methods

Lines 816011-816033 define the artifact RPC methods:

```
listBackgroundComposerArtifacts:
    name: "ListBackgroundComposerArtifacts"
    kind: Unary

getBackgroundComposerArtifact:
    name: "GetBackgroundComposerArtifact"
    kind: Unary

getBackgroundComposerArtifactBytes:
    name: "GetBackgroundComposerArtifactBytes"
    kind: Unary

streamBackgroundComposerArtifact:
    name: "StreamBackgroundComposerArtifact"
    kind: ServerStreaming
```

## Slack Integration

The artifact system includes Slack integration fields (lines 807371-807381, 807424-807428):
- `slack_upload_url`: Alternative upload endpoint for Slack file sharing
- `slack_file_id`: ID returned after successful Slack upload

This suggests artifacts can be shared to Slack channels/threads as part of the cloud agent workflow.

## Upload Flow Analysis

Based on the schema structure, the upload flow appears to be:

1. **List Artifacts**: Client calls `ListArtifacts()` to get current artifact metadata and upload status
2. **Request Upload**: Server provides `ArtifactUploadInstruction` with presigned URL
3. **Direct Upload**: Client uploads file directly to cloud storage using presigned URL with specified method and headers
4. **Status Tracking**: Upload progress tracked via `bytes_uploaded`, `status`, and `upload_attempts` fields
5. **Dispatch Result**: Server returns `ArtifactUploadDispatchResult` with status (ACCEPTED, REJECTED, or SKIPPED_ALREADY_IN_PROGRESS)

## Download Flow Analysis

For artifact downloads (typically from cloud agent to IDE):

1. **Get Artifact URL**: Call `GetBackgroundComposerArtifact()` with bc_id and path
2. **Direct Download**: Server returns presigned URL in response
3. **Alternative: Get Bytes**: Call `GetBackgroundComposerArtifactBytes()` for direct content
4. **Streaming**: For large files, use `StreamBackgroundComposerArtifact()` for chunked transfer

## Security Considerations

- **Presigned URLs**: Time-limited URLs for direct cloud storage access
- **Path Validation**: Absolute paths used for unambiguous file identification
- **Error Handling**: Detailed error tracking with `last_error` and attempt counting
- **Idempotency**: `upload_id` allows retry and deduplication logic

## Related Analysis

- TASK-14: Cloud Agent Storage - General blob storage architecture
- TASK-87: Blob Storage - Detailed blob storage implementation
- TASK-75: DevContainer Snapshot - Snapshot presigned URL usage

## Reconstruction (Protobuf Format)

```protobuf
syntax = "proto3";
package agent.v1;

enum ArtifactUploadStatus {
  ARTIFACT_UPLOAD_STATUS_UNSPECIFIED = 0;
  ARTIFACT_UPLOAD_STATUS_NOT_STARTED = 1;
  ARTIFACT_UPLOAD_STATUS_IN_PROGRESS = 2;
  ARTIFACT_UPLOAD_STATUS_COMPLETED = 3;
  ARTIFACT_UPLOAD_STATUS_FAILED = 4;
}

enum ArtifactUploadDispatchStatus {
  ARTIFACT_UPLOAD_DISPATCH_STATUS_UNSPECIFIED = 0;
  ARTIFACT_UPLOAD_DISPATCH_STATUS_ACCEPTED = 1;
  ARTIFACT_UPLOAD_DISPATCH_STATUS_REJECTED = 2;
  ARTIFACT_UPLOAD_DISPATCH_STATUS_SKIPPED_ALREADY_IN_PROGRESS = 3;
}

message ListArtifactsRequest {}

message ArtifactUploadMetadata {
  string absolute_path = 1;
  uint64 size_bytes = 2;
  int64 updated_at_unix_ms = 3;
  ArtifactUploadStatus status = 4;
  uint64 bytes_uploaded = 5;
  string last_error = 6;
  uint32 upload_attempts = 7;
  int64 last_started_at_unix_ms = 8;
  int64 last_finished_at_unix_ms = 9;
  string upload_id = 10;
}

message ListArtifactsResponse {
  repeated ArtifactUploadMetadata artifacts = 1;
}

message ArtifactUploadInstruction {
  string absolute_path = 1;
  string upload_url = 2;
  string method = 3;
  map<string, string> headers = 4;
  optional string content_type = 5;
  optional string slack_upload_url = 6;
  optional string slack_file_id = 7;
}

message UploadArtifactsRequest {
  repeated ArtifactUploadInstruction uploads = 1;
}

message ArtifactUploadDispatchResult {
  string absolute_path = 1;
  ArtifactUploadDispatchStatus status = 2;
  string message = 3;
  optional string slack_file_id = 4;
}

message UploadArtifactsResponse {
  repeated ArtifactUploadDispatchResult results = 1;
}

service ControlService {
  rpc ListArtifacts(ListArtifactsRequest) returns (ListArtifactsResponse);
  rpc UploadArtifacts(UploadArtifactsRequest) returns (UploadArtifactsResponse);
}
```

```protobuf
syntax = "proto3";
package aiserver.v1;

message BackgroundComposerArtifact {
  string absolute_path = 1;
  int64 size_bytes = 2;
  int64 updated_at_unix_ms = 3;
}

message ListBackgroundComposerArtifactsRequest {
  string bc_id = 1;
}

message ListBackgroundComposerArtifactsResponse {
  repeated BackgroundComposerArtifact artifacts = 1;
}

message GetBackgroundComposerArtifactRequest {
  string bc_id = 1;
  string absolute_path = 2;
}

message GetBackgroundComposerArtifactResponse {
  string url = 1;
}

message GetBackgroundComposerArtifactBytesRequest {
  string bc_id = 1;
  string absolute_path = 2;
}

message GetBackgroundComposerArtifactBytesResponse {
  bytes content = 1;
  string content_type = 2;
}

message StreamBackgroundComposerArtifactRequest {
  string bc_id = 1;
  string absolute_path = 2;
}

message StreamBackgroundComposerArtifactResponse {
  bytes content_chunk = 1;
  string content_type = 2;
  int64 total_size = 3;
}

service BackgroundComposerService {
  rpc ListBackgroundComposerArtifacts(ListBackgroundComposerArtifactsRequest)
      returns (ListBackgroundComposerArtifactsResponse);
  rpc GetBackgroundComposerArtifact(GetBackgroundComposerArtifactRequest)
      returns (GetBackgroundComposerArtifactResponse);
  rpc GetBackgroundComposerArtifactBytes(GetBackgroundComposerArtifactBytesRequest)
      returns (GetBackgroundComposerArtifactBytesResponse);
  rpc StreamBackgroundComposerArtifact(StreamBackgroundComposerArtifactRequest)
      returns (stream StreamBackgroundComposerArtifactResponse);
}
```

## Notes

- No explicit download method exists in `agent.v1.ControlService` - downloads appear to be handled through the `aiserver.v1.BackgroundComposerService`
- The artifact system supports both synchronous (bytes) and streaming (chunk) retrieval
- Slack integration suggests artifacts may be used for sharing results/reports from cloud agent runs
- The upload instruction includes HTTP headers, allowing for authentication tokens, content-disposition, etc.
