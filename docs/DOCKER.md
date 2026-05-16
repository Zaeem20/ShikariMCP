# Docker

## Images

| Image | File | Contents |
|-------|------|----------|
| `shikari` | `docker/Dockerfile` | Base image with core profile tools |
| `shikari:core` | `docker/Dockerfile.core` | Core profile only |
| `shikari:web` | `docker/Dockerfile.web` | Core + web profile extras |
| `shikari:full` | `docker/Dockerfile.full` | All profiles combined |

## Build

```bash
# Base image (includes core profile verification)
docker build -t shikari -f docker/Dockerfile .

# Profile-specific images
docker build -t shikari:core -f docker/Dockerfile.core .
docker build -t shikari:web -f docker/Dockerfile.web .
docker build -t shikari:full -f docker/Dockerfile.full .
```

## Run

```bash
# HTTP mode with API key
docker run -p 8080:8080 \
  -e SHIKARI_API_KEY=your-secret-key \
  shikari

# With docker-compose
export SHIKARI_API_KEY=your-secret-key
docker compose up -d
```

## Environment

The Docker image sets safe defaults:

```
SHIKARI_TRANSPORT=streamable-http
SHIKARI_HOST=0.0.0.0
SHIKARI_PORT=8080
SHIKARI_ENABLE_GENERATED_TOOLS=false
SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS=false
SHIKARI_AUDIT_ENABLED=true
SHIKARI_LOG_LEVEL=INFO
```

Override any variable at runtime:

```bash
docker run -p 8080:8080 \
  -e SHIKARI_API_KEY=your-key \
  -e SHIKARI_ENABLE_ACTIVE_TOOLS=true \
  -e SHIKARI_TOOL_PROFILE=full \
  shikari
```

## Verification

The base image runs `shikari tools verify --profile core --json` during build. A failed verification causes the build to fail.

## Adding Tools

Extend the Dockerfile to include additional packages:

```dockerfile
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    your-tool-here \
    && rm -rf /var/lib/apt/lists/*
```

Or create a new profile manifest and corresponding Dockerfile following the pattern in `docker/Dockerfile.web`.
