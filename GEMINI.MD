# Project Overview

Name: glitch-hunt-ingestion
Mission: Building the API for a zero-dependency, resilient data bridge that transforms local file-system events into structured cloud data.
Architecture Pattern: Event-Driven with Ephemeral Handshake.


## General Instructions

- Framework python and fastapi as well as UV.
- The general architecture is depecited in the plantUML file in @docs/architecture.plantuml
- Package Manager: uv
- State Management (Short-term): Redis Cache (glitch-hunt-redis) 
- Event Pipeline (Async): Redis Streams
- Permanent Storage: PostgreSQL (glitch-hunt-postgres)
- Cloud Storage: MINIO (Binary Data)
- My docker-compose should spin up the redis and postgress stuff for local run.

## --- MinIO Configurations ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "s3.my-basement.cloud")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "pusteblume123!")
MINIO_REGION = os.getenv("MINIO_REGION", "eu-central-1")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "glitch-hunt-dev")

## Functional Requirements and Core API ENdpoints to Implement

### POST /v1/ingest/request
Purpose: Initiates the "Handshake." Validates metadata and provides a temporary S3 "Ticket."

Data Contract (Request):
{
  "device_id": "string",
  "filename": "string",
  "file_size_bytes": "int",
  "sha256_checksum": "string(64)",
  "context": ["string", "string"], 
  "metadata": {"key": "value"},
  "timestamp": "ISO8601-UTC"
}

Internal Logic:
Generate correlation_id (UUID4).
Calculate S3 Key: s3://{bucket}/{context_joined}/{YYYY-MM-DD}/{filename}.
Persist to Redis: Store full payload in Redis Cache (handshake:{id}) with a 30-minute TTL.
Sign URL: Generate a Boto3 S3 PUT Presigned URL.
Response: 
{
  "correlation_id": "uuid",
  "upload_url": "https://s3...",
  "expires_at": "ISO8601-UTC"
}

### POST /v1/ingest/confirm
Purpose: Finalizes the transfer. Triggers the Orchestrator and authorizes the Edge to prune.
Data Contract (Request):
{
  "correlation_id": "uuid",
  "status": "SUCCESS | FAILED",
  "error_message": "string (optional)"
}
Glitch-Hunt
Custom Gem
This GEMINI.MD file is designed to be a "Source of Truth" for an AI agent (like myself) or a developer to understand the exact technical constraints, data contracts, and architectural flow of your project.

You can create this file in your root directory and paste the following content:
