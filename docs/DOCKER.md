# Docker

## Supported Image

`docker/Dockerfile` is the production image. It installs and verifies the 12-tool `core` profile with pinned Go releases, Nikto, SQLMap, Trivy, and the core SecLists wordlist.

Broader workstation profiles should be installed on the host with `scripts/install-tools.sh`. They are not bundled into the production container because credential and forensic suites significantly expand privileges, size, and attack surface.

## Compose

```bash
cp .env.docker.example .env
# Replace SHIKARI_API_KEY with a long random value.
docker compose up --build
```

Connect to `http://127.0.0.1:8080/mcp` using `Authorization: Bearer <key>`.

Compose applies:

- localhost-only port publishing by default
- read-only root filesystem
- non-root application user
- `no-new-privileges`
- dropped Linux capabilities except `NET_RAW`
- PID limit and bounded `/tmp`
- persistent audit logs and artifacts in `shikari-data`
- persistent tool configuration and templates in `shikari-home`

## Build And Verify

```bash
docker build -t shikari-mcp:local -f docker/Dockerfile .
docker run --rm --entrypoint shikari-mcp shikari-mcp:local \
  tools verify --profile core --json
```

The Docker build runs the same profile verification and fails if a required core binary is absent.

## Enable Authorized Active Scans

Set both the active flag and a narrow target allowlist in `.env`:

```dotenv
SHIKARI_ENABLE_ACTIVE_TOOLS=true
SHIKARI_TARGET_ALLOWLIST=example.com,10.10.0.0/16
```

## Rate Limiting

The container enables rate limiting by default (60 req/s per IP, 100 burst). To adjust or disable:

```dotenv
SHIKARI_RATE_LIMIT_RPS=120    # Increase for trusted networks
SHIKARI_RATE_LIMIT_BURST=200  # Higher burst for CI/automation
# SHIKARI_RATE_LIMIT_RPS=0    # Uncomment to disable entirely
```

Remote active tools remain disabled in the container. The default Compose deployment uses local mode and binds only to `127.0.0.1`.

## Data

The `shikari-data` volume contains:

```text
/app/.shikari/audit.jsonl
/app/.shikari/artifacts/
```

Large tool outputs remain in this volume and are read in bounded chunks through `shikari_read_artifact`.
