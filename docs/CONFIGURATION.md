# Configuration

## Environment Variables

| Variable | Default | Purpose |
|---|---:|---|
| `SHIKARI_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `SHIKARI_HOST` | `127.0.0.1` | HTTP bind address |
| `SHIKARI_PORT` | `8080` | HTTP port |
| `SHIKARI_API_KEY` | empty | Required bearer key for HTTP |
| `SHIKARI_ALLOW_UNAUTHENTICATED_HTTP` | `false` | Development-only auth opt-out |
| `SHIKARI_LOCAL_MODE` | `false` | Permit local-scope tools over local HTTP |
| `SHIKARI_HTTP_JSON_RESPONSE` | `false` | Use JSON responses instead of SSE |
| `SHIKARI_HTTP_STATELESS` | `false` | Disable HTTP sessions and event replay |
| `SHIKARI_HTTP_ALLOWED_HOSTS` | local hosts | Allowed Host header patterns |
| `SHIKARI_HTTP_ALLOWED_ORIGINS` | local origins | Allowed browser Origin patterns |
| `SHIKARI_HTTP_EVENT_TTL` | `3600` | Replayable event lifetime in seconds |
| `SHIKARI_HTTP_RETRY_INTERVAL_MS` | `2000` | SSE retry interval |
| `SHIKARI_RATE_LIMIT_RPS` | `60` | Per-IP requests per second (0 to disable) |
| `SHIKARI_RATE_LIMIT_BURST` | `100` | Per-IP burst capacity |
| `SHIKARI_TRUST_X_FORWARDED_FOR` | `false` | Honor X-Forwarded-For header for client IP (only behind trusted proxy) |
| `SHIKARI_TIMEOUT` | `300` | Maximum command duration |
| `SHIKARI_MAX_CONCURRENT` | `10` | Concurrent subprocess limit |
| `SHIKARI_MAX_OUTPUT_CHARS` | `50000` | In-memory output limit |
| `SHIKARI_MAX_PARSER_BYTES` | `10000000` | Largest artifact parsed in memory |
| `SHIKARI_MAX_BACKGROUND_RUNS` | `100` | Background run history/capacity |
| `SHIKARI_MAX_INPUT_CHARS` | `1000000` | Total input size per tool call |
| `SHIKARI_MAX_TARGETS_PER_RUN` | `5000` | Maximum newline-delimited targets |
| `SHIKARI_ARTIFACT_DIR` | `.shikari/artifacts` | Confined artifact directory |
| `SHIKARI_DEFAULT_WORDLIST` | SecLists common | Default ffuf/Gobuster wordlist |
| `SHIKARI_TOOL_PROFILE` | `core` | Manifest profile |
| `SHIKARI_ENABLE_LEGACY_TOOLS` | `true` | Expose direct compatibility wrappers |
| `SHIKARI_ENABLE_GENERATED_TOOLS` | `true` | Expose generated wrappers with legacy mode |
| `SHIKARI_ENABLE_EXPERIMENTAL_TOOLS` | `true` | Expose experimental agents/wrappers |
| `SHIKARI_REQUIRE_TOOL_DEPENDENCIES` | `false` | Hide wrappers with missing binaries |
| `SHIKARI_ENABLE_ACTIVE_TOOLS` | `true` | Permit active scans |
| `SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS` | `false` | Permit active scans over remote HTTP |
| `SHIKARI_ENABLE_OFFENSIVE_TOOLS` | `true` | Permit offensive profile operations |
| `SHIKARI_ENABLE_CREDENTIAL_TOOLS` | `true` | Permit credential testing tools |
| `SHIKARI_TARGET_ALLOWLIST` | empty | Authorized domains, CIDRs, or path roots |
| `SHIKARI_AUDIT_ENABLED` | `true` | Write JSONL audit events |
| `SHIKARI_AUDIT_LOG_PATH` | `.shikari/audit.jsonl` | Audit log path |
| `SHIKARI_LOG_LEVEL` | `INFO` | Runtime log level |

## CLI

Run `shikari-mcp --help` for transport and policy flags. Environment settings cover resource limits and HTTP event behavior.

Key HTTP flags:

| Flag | Env Var | Purpose |
|------|---------|---------|
| `--transport http` | `SHIKARI_TRANSPORT` | Use Streamable HTTP transport |
| `--api-key KEY` | `SHIKARI_API_KEY` | Bearer token for HTTP auth |
| `--local` | `SHIKARI_LOCAL_MODE` | Allow local-scope tools over HTTP |
| `--rate-limit-rps N` | `SHIKARI_RATE_LIMIT_RPS` | Per-IP request rate (default: 60, 0 to disable) |
| `--rate-limit-burst N` | `SHIKARI_RATE_LIMIT_BURST` | Per-IP burst capacity (default: 100) |
| `--trust-x-forwarded-for` | `SHIKARI_TRUST_X_FORWARDED_FOR` | Honor X-Forwarded-For header for client IP |
| `--http-json-response` | `SHIKARI_HTTP_JSON_RESPONSE` | JSON instead of SSE |
| `--http-stateless` | `SHIKARI_HTTP_STATELESS` | Disable session state |
| `--http-allowed-hosts H` | `SHIKARI_HTTP_ALLOWED_HOSTS` | Comma-separated Host patterns |
| `--http-allowed-origins O` | `SHIKARI_HTTP_ALLOWED_ORIGINS` | Comma-separated Origin patterns |

HTTP fails closed without an API key. Local-scope tools remain unavailable over remote HTTP even when active tools are enabled.

## Single-User Self-Hosted Defaults

For a standalone Kali workstation, all tool categories are enabled by default so every tool and agent is available immediately. If you run ShikariMCP in a shared or remote environment, set the following variables to restore the safer defaults:

```bash
SHIKARI_ENABLE_LEGACY_TOOLS=false
SHIKARI_ENABLE_GENERATED_TOOLS=false
SHIKARI_ENABLE_EXPERIMENTAL_TOOLS=false
SHIKARI_ENABLE_ACTIVE_TOOLS=false
SHIKARI_ENABLE_OFFENSIVE_TOOLS=false
SHIKARI_ENABLE_CREDENTIAL_TOOLS=false
SHIKARI_REQUIRE_TOOL_DEPENDENCIES=true
```

## Proxy Configuration

When deploying behind a reverse proxy, set `SHIKARI_TRUST_X_FORWARDED_FOR=true` only if your proxy overwrites the `X-Forwarded-For` header. Without a trusted proxy, this header is user-controlled and can be spoofed to bypass rate limiting.
