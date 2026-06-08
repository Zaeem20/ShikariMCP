# ShikariMCP

Local-first Model Context Protocol server for authorized security testing. Shikari connects AI clients to real security binaries through reviewed manifests, bounded subprocess execution, structured evidence, and non-blocking background jobs.

## Production Baseline

- `stdio` and stateful Streamable HTTP transports
- API-key authentication for HTTP
- resumable HTTP event storage and Host/Origin validation
- background submit, poll, cancel, and artifact-read APIs
- process-tree termination on timeout or MCP cancellation
- bounded in-memory output with complete output saved as artifacts
- safety gates for active, offensive, and credential tooling
- exact domain, CIDR, and filesystem allowlist checks
- cloud metadata endpoint blocking
- 12 verified core integrations and four implemented workflows

The large compatibility wrapper catalog is retained but hidden by default. The production interface is the manifest runner, which prevents direct wrappers from bypassing policy and output handling.

## Core Integrations

| Tool | ID | Use |
|---|---|---|
| Nmap | `nmap_scan` | Service and version discovery |
| Subfinder | `subfinder_enum` | Passive subdomain discovery |
| httpx | `httpx_probe` | HTTP probing and technology detection |
| Nuclei | `nuclei_scan` | Rate-limited template scanning |
| Naabu | `naabu_scan` | Port discovery |
| Katana | `katana_crawl` | Endpoint crawling |
| ffuf | `ffuf_fuzz` | Web content discovery |
| Gobuster | `gobuster_dir` | Directory discovery |
| Nikto | `nikto_scan` | Web server checks |
| SQLMap | `sqlmap_scan` | Conservative SQL injection checks |
| Trivy | `trivy_scan` | Filesystem and dependency scanning |
| Whois | `whois_lookup` | Domain and IP registration context |

Additional `recon`, `web`, `cloud`, `forensics`, and explicitly gated `offensive` profiles are documented in [Tools and Profiles](docs/TOOLS.md).

## Install

Python 3.11 or newer is required.

```bash
git clone https://github.com/Zaeem20/ShikariMCP.git
cd ShikariMCP
uv sync --group dev
```

Install the external core binaries on Debian, Ubuntu, Kali, or macOS:

```bash
./scripts/install-tools.sh --profile core
./scripts/verify-tools.sh --profile core --json
```

Preview installer actions without changing the machine:

```bash
./scripts/install-tools.sh --profile core --dry-run
```

## Run With Stdio

```bash
uv run shikari --transport stdio
```

Example MCP client configuration:

```json
{
  "mcpServers": {
    "shikari": {
      "command": "uv",
      "args": ["run", "shikari", "--transport", "stdio"],
      "cwd": "/absolute/path/to/ShikariMCP"
    }
  }
}
```

## Run With Streamable HTTP

HTTP requires authentication unless the development-only opt-out is explicitly used.

```bash
uv run shikari \
  --transport http \
  --host 127.0.0.1 \
  --port 8080 \
  --api-key "replace-with-a-long-random-secret" \
  --local
```

Connect to `http://127.0.0.1:8080/mcp` with:

```text
Authorization: Bearer replace-with-a-long-random-secret
```

The default HTTP mode is stateful SSE with replayable events during the server process lifetime. JSON-only and stateless modes exist for simple integrations, but interactive AI clients should use the default.

## Non-Blocking Runs

Long scans should use the job API so the AI client is not held inside one MCP request:

1. Call `shikari_submit_verified_tool`.
2. Poll `shikari_get_run` or inspect `shikari_list_runs`.
3. Retrieve large evidence with `shikari_read_artifact`.
4. Stop work with `shikari_cancel_run`.

`shikari_run_verified_tool` remains useful for dry runs and short commands. It defaults to `dry_run=true`.

## Docker

The production container includes the verified core profile only. It runs as a non-root user with a read-only root filesystem under Compose.

```bash
cp .env.docker.example .env
# Set a strong SHIKARI_API_KEY in .env
docker compose up --build
```

The MCP endpoint is `http://127.0.0.1:8080/mcp`.

Direct image usage:

```bash
docker build -t shikari:local -f docker/Dockerfile .
docker run --rm -p 127.0.0.1:8080:8080 \
  --cap-drop ALL --cap-add NET_RAW \
  --security-opt no-new-privileges \
  -e SHIKARI_API_KEY="replace-with-a-long-random-secret" \
  -v shikari-data:/app/.shikari \
  -v shikari-home:/home/shikari \
  shikari:local
```

See [Docker](docs/DOCKER.md) for capabilities, persistence, and verification.

## Safety

Active scans are disabled until enabled:

```bash
uv run shikari \
  --transport stdio \
  --enable-active-tools \
  --target-allowlist "example.com,10.10.0.0/16,/absolute/lab/path"
```

Offensive and credential profiles have separate opt-ins. Remote HTTP also requires `--enable-remote-active-tools`. Use only against systems you own or are explicitly authorized to test.

Legacy direct wrappers are disabled by default. Compatibility testing requires `--enable-legacy-tools`; generated wrappers additionally require `--enable-generated-tools`.

## Verify

```bash
uv run pytest tests -q
uv run ruff check src tests
uv run shikari tools verify --profile core --json
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Production Readiness Report](SHIKARI_PRODUCTION_READINESS_REPORT.md)
- [Tools and Profiles](docs/TOOLS.md)
- [Configuration](docs/CONFIGURATION.md)
- [MCP Clients](docs/MCP_CLIENTS.md)
- [Docker](docs/DOCKER.md)
- [Development](docs/DEVELOPMENT.md)

## License

MIT. See [LICENSE](LICENSE).
