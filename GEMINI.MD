# Project Overview

Name: glitch-hunt-ingestion
Mission: Building the API for a zero-dependency, resilient data bridge that transforms local file-system events into structured cloud data.
Architecture Pattern: Event-Driven with Ephemeral Handshake.


## General Instructions

- Framework python and fastapi as well as UV.
- The general architecture of the overall application is depicted in the plantUML file in @docs/architecture.plantuml. Our focus in the API
- Package Manager: uv
- State Management (Short-term): Redis Cache (glitch-hunt-redis) 
- Event Pipeline (Async): Redis Streams
- Permanent Storage: PostgreSQL (glitch-hunt-postgres)
- Cloud Storage: MINIO (Binary Data)
- My docker-compose should spin up the redis and postgress stuff for local run
- When creating Dockerfiles use multi staging if applicable. Im targeting fast builds
- Use Helm  for deployment to k8s tasks
- You can access the k8s cluster via kubectl
- Use a own script/ folder to store all scripts
- You can use kubectl command to access the k8s cluster and glitch-hunt-namespace
- Before we implement stuff we always create a implementation strategy together - means we brainstorm and you actively ask questions to sharpen the requirements!

