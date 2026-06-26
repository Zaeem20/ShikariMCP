# Architecture

This document explains how ShikariMCP is structured, how requests flow through the system, and how each component contributes to safe, non-blocking security tool execution.

## System Overview

![ShikariMCP Architecture](../assets/shikari-mcp-architecture.png)

The diagram above shows the full request flow: AI clients connect via stdio or Streamable HTTP, pass through the HTTP middleware stack (rate limiter → Host/Origin validation → API key auth), reach the MCP Tool Router (12 MCP tools), then flow through input validation, the policy engine (risk-class gating, target allowlist, cloud metadata block + DNS TOCTOU re-check), the Tool Runner (manifest → command → execute → parse), and finally to external security binaries. Background jobs are managed by the Run Manager. All events are written to the JSONL audit log. Tool sources span three tiers: 50 manifest-verified tools, 305 `@shikari_tool` wrappers, and 51 agents.

## Project Structure

```mermaid
flowchart LR
    subgraph src["src/shikari/"]
        S["server.py<br/>Entry point + CLI"]
        C["config.py<br/>Configuration"]

        subgraph core["core/"]
            C1["registry.py"]
            C2["executor.py"]
            C3["auth.py"]
            C4["policy.py"]
            C5["tool_runner.py"]
            C6["tool_manifest.py"]
            C7["run_manager.py"]
            C8["rate_limiter.py"]
            C9["http_security.py"]
            C10["artifacts.py"]
            C11["audit.py"]
            C12["input_validation.py"]
            C13["validator.py"]
        end

        subgraph manifests["manifests/tools/"]
            M1["core.json"]
            M2["recon.json"]
            M3["web.json"]
            M4["cloud.json"]
            M5["forensics.json"]
            M6["offensive.json"]
            M7["osint.json"]
        end

        subgraph parsers["parsers/"]
            P1["models.py<br/>ParsedOutput"]
            P2["dispatch.py"]
            P3["nmap, subfinder, httpx<br/>nuclei, ffuf, gobuster<br/>nikto, sqlmap, trivy<br/>sherlock, exiftool<br/>greynoise, virustotal<br/>theharvester"]
        end

        subgraph agents["agents/"]
            A1["_base_agent.py"]
            A2["workflow/ - 13"]
            A3["intelligence/ - 10"]
            A4["infrastructure/ - 8"]
            A5["domain/ - 10"]
            A6["offensive/ - 5"]
            A7["defensive/ - 5"]
        end

        subgraph tools["tools/ - 35 categories"]
            T1["_base.py<br/>@shikari_tool decorator"]
            T2["reconnaissance - 65"]
            T3["enumeration - 30"]
            T4["osint - 23"]
            T5["+ 32 more categories"]
        end
    end

    subgraph tests["tests/"]
        TS["152 unit tests"]
    end

    subgraph scripts["scripts/"]
        SC1["install-tools.sh"]
        SC2["verify-tools.sh"]
    end

    subgraph docker["docker/"]
        DK["Dockerfile + compose"]
    end
```

## Core Components

### Tool Discovery

Tools are auto-discovered from `src/shikari/tools/` by scanning for functions decorated with `@shikari_tool`. Each tool declares:

| Property | Values | Purpose |
|----------|--------|---------|
| `scope` | `LOCAL`, `REMOTE`, `BOTH` | Where the tool can run |
| `binary` | e.g. `"nmap"` | Required CLI binary |
| `category` | e.g. `"reconnaissance"` | Capability grouping |
| `capabilities` | e.g. `["active_network"]` | Risk-class gating |
| `quality` | `VERIFIED`, `EXPERIMENTAL`, `GENERATED` | Trust tier |

The registry filters tools based on transport mode and runtime configuration. By default, only `shikari.agents.workflow` is discovered (4 production workflows). Use `--enable-legacy-tools` or `--enable-experimental-tools` to expose the full catalog.

### Manifest System

Manifests in `src/shikari/manifests/tools/` define verified tools with:

| Field | Example | Purpose |
|-------|---------|---------|
| `command_templates` | `{"safe": {"argv": ["nmap", "{target}"]}}` | Command with placeholder substitution |
| `output_format` | `"jsonl"`, `"xml"`, `"text"` | Determines parser routing and artifact kind |
| `capabilities` | `["active_network"]` | Risk-class gating |
| `approval` | `"active_tools"`, `"none"` | Required safety gate |
| `parser` | `"shikari.parsers.nmap.parse_xml"` | Dotted reference to output parser |
| `scope` | `"local"`, `"both"` | Transport availability |
| `install` | `{"apt": ["nmap"]}` | Installation hints |

The `tool_runner.py` module builds commands from these templates instead of each wrapper inventing its own command line. This ensures consistent policy enforcement, output handling, and artifact storage.

### Execution Flow

```mermaid
sequenceDiagram
    participant AI as AI Client
    participant SRV as ShikariMCP
    participant POL as Policy Engine
    participant EX as Executor
    participant BIN as Security Binary
    participant PA as Parser
    participant AR as Artifact Store

    AI->>SRV: shikari_run_verified_tool(tool_id, inputs, dry_run=false)
    SRV->>SRV: Load manifest, build command from template
    SRV->>POL: evaluate_tool_policy(tool, inputs)
    POL->>POL: Check allowlist, metadata block, risk gates
    POL-->>SRV: allowed / blocked + reason

    alt blocked
        SRV-->>AI: {status: "blocked", errors: [reason]}
    else allowed
        SRV->>SRV: TOCTOU re-check (DNS re-resolution)
        SRV->>EX: execute_command(argv, timeout, stdin)
        EX->>BIN: asyncio.create_subprocess_exec(*argv)
        BIN-->>EX: stdout + stderr (bounded)
        EX-->>SRV: result (output, returncode, artifacts)

        SRV->>AR: Save full output to artifact file
        SRV->>PA: parse_tool_output(parser_ref, raw)
        PA-->>SRV: ParsedOutput (assets, services, findings)
        SRV-->>AI: {status, findings, assets, artifacts, raw_output}
    end
```

The five stages of manifest-backed execution:

1. **Dry-run** — `dry_run_verified_tool()` builds the command preview without executing. Defaults to `dry_run=true` for safety.
2. **Policy check** — `evaluate_tool_policy()` validates safety gates, target allowlist, and cloud metadata blocking.
3. **TOCTOU re-check** — Immediately before execution, targets are re-resolved to detect DNS rebinding attacks that could bypass the metadata block.
4. **Execution** — `execute_command()` runs the subprocess via `asyncio.create_subprocess_exec` (no shell), with timeout and process-tree termination.
5. **Parsing + Storage** — Raw output is parsed into `ParsedOutput` and stored as artifacts. Only bounded summaries enter the LLM context; full output is read on demand via `shikari_read_artifact`.

### Parser System

Each parser converts tool-specific output into a common `ParsedOutput` model:

```mermaid
flowchart LR
    RAW["Raw Tool Output"] --> P["Parser"]
    P --> PO["ParsedOutput"]

    subgraph PO["ParsedOutput"]
        A["Assets<br/>hosts, domains, IPs<br/>social profiles, geolocations"]
        S["Services<br/>port, protocol, product, version"]
        E["Endpoints<br/>URL, status, technologies"]
        F["Findings<br/>title, severity, evidence"]
    end
```

| Parser | Tool | Extracts |
|--------|------|---------|
| `nmap.parse_xml` | nmap | Services, ports, OS detection |
| `subfinder.parse_jsonl` | subfinder | Subdomain assets |
| `httpx.parse_jsonl` | httpx | Live endpoints, tech detection |
| `nuclei.parse_jsonl` | nuclei | Vulnerability findings |
| `sherlock.parse_csv` | sherlock | Social media profiles |
| `exiftool.parse_json` | exiftool | Metadata + GPS coordinates |
| `exiftool.parse_gps` | exiftool | Geolocation assets |
| `greynoise.parse_json` | greynoise | IP classification (benign/malicious) |
| `virustotal.parse_json` | vt | Scan stats (malicious/suspicious counts) |
| `theharvester.parse_text` | theHarvester | Emails, hosts, URLs |

Parsers are dispatched by tool ID through `dispatch.py`. Each parser handles malformed/empty input gracefully and never raises.

### Agent System

All agents extend `BaseAgent` and follow a four-phase workflow:

```mermaid
flowchart LR
    P["1. Plan<br/>Determine tools and order"] --> E["2. Execute<br/>Run tools, pass results"]
    E --> A["3. Analyze<br/>Parse outputs, correlate findings"]
    A --> R["4. Report<br/>Structured results and evidence"]
```

| Agent Tier | Count | Execution | Exposed by default |
|------------|:-----:|-----------|:------------------:|
| Production workflows | 4 | `execute_verified_plan` (manifest-backed) | Yes |
| Catalog agents | 47 | `execute_command` (raw subprocess) | No (`--enable-experimental-tools`) |

Production workflows run manifest-backed tools with full policy enforcement. Catalog agents execute real multi-step CLI plans defined in `_catalog.py` but use raw subprocess execution — they should be promoted to `execute_verified_plan` to inherit full policy enforcement.

See [Agents](AGENTS.md) for the full catalog.

### Background Job System

```mermaid
flowchart TB
    subgraph Submit["shikari_submit_verified_tool"]
        S1["Create run_id"] --> S2["Queue in Run Manager"] --> S3["Return run_id immediately"]
    end

    subgraph Execute["Background Execution"]
        E1["Pick up from queue"] --> E2["Run via Tool Runner"]
        E2 --> E3["Store result and artifacts"]
    end

    subgraph Poll["shikari_get_run"]
        P1["Look up run_id"] --> P2["Return status and findings"]
    end

    subgraph Cancel["shikari_cancel_run"]
        C1["Set status = cancelling"] --> C2["task.cancel"] --> C3["Kill process tree"]
    end

    Submit --> Execute
    Execute -.->|status update| Poll
    Cancel -.->|terminates| Execute
```

The Run Manager maintains a bounded history of background runs (default 100). Each run has a lifecycle: `queued` → `running` → `success` / `failed` / `cancelled` / `timeout`. Background runs are capped at `default_timeout` (300s) even if the manifest specifies a longer timeout.

## Safety Controls

```mermaid
flowchart TB
    REQ["Incoming Tool Request"] --> V1{"MCP Boundary Validation<br/>Pydantic models"}
    V1 -->|reject| ERR["Error: invalid input"]
    V1 -->|accept| V2{"Input Validation<br/>NUL bytes, option prefix, size limits"}
    V2 -->|reject| ERR
    V2 -->|accept| P1{"Policy Engine"}

    subgraph PE["Policy Checks"]
        P1 --> P2{"Risk-class gate<br/>active, offensive, credential"}
        P2 -->|blocked| BLK["Blocked: requires opt-in"]
        P2 -->|allowed| P3{"Target allowlist<br/>domain, CIDR, path"}
        P3 -->|not in list| BLK
        P3 -->|in list| P4{"Cloud metadata block<br/>169.254.169.254 etc"}
        P4 -->|metadata IP| BLK
        P4 -->|safe| P5{"Scope check<br/>local vs remote"}
        P5 -->|local-only, remote HTTP| BLK
        P5 -->|ok| ALLOW["Execute"]
    end

    BLK --> RESP["Return blocked and reason"]
    ALLOW --> EXEC["Run subprocess"]
```

| Control | What It Prevents |
|---------|------------------|
| MCP boundary validation | Invalid tool IDs, unknown profiles, oversized inputs, path traversal |
| Input validation | NUL bytes, option-prefix injection, target count limits |
| Risk-class gating | Active/offensive/credential tools without explicit opt-in |
| Target allowlist | Scanning unauthorized hosts, domains, CIDRs, or paths |
| Cloud metadata blocking | Access to `169.254.169.254` and equivalent endpoints |
| DNS TOCTOU re-check | DNS rebinding attacks between policy check and execution |
| Scope enforcement | Local-only tools exposed over remote HTTP |
| Dry-run default | Accidental execution without command preview |
| Output bounding | Unbounded memory growth from large tool output |
| Process-tree termination | Zombie processes on timeout or cancellation |
| Background timeout cap | Long-running manifests blocking background slots indefinitely |

## HTTP Security Stack

```mermaid
flowchart LR
    REQ["HTTP Request"] --> MW1["1. Rate Limiter<br/>per-IP token bucket<br/>60 req/s, 100 burst"]
    MW1 -->|429| R429["Too Many Requests<br/>Retry-After"]
    MW1 -->|ok| MW2["2. Host/Origin Validation<br/>DNS rebinding protection<br/>security headers"]
    MW2 -->|400| R400["Invalid Host or Origin"]
    MW2 -->|ok| MW3["3. API Key Auth<br/>constant-time compare<br/>Bearer token"]
    MW3 -->|401| R401["Unauthorized"]
    MW3 -->|ok| MCP["FastMCP Handler"]
    MCP --> TOOLS["Tool Router"]
```

| Layer | Default | Configurable |
|-------|---------|-------------|
| Rate limiter | 60 req/s, 100 burst per IP | `--rate-limit-rps`, `--rate-limit-burst` (0 to disable) |
| X-Forwarded-For | Ignored (use direct client IP) | `--trust-x-forwarded-for` (only behind trusted proxy) |
| Host validation | localhost, 127.0.0.1, [::1] | `--http-allowed-hosts` |
| Origin validation | localhost origins | `--http-allowed-origins` |
| Auth | Required (Bearer token) | `--api-key`, `--allow-unauthenticated-http` (dev only) |
| Security headers | `nosniff`, `DENY`, `no-referrer` on errors | Automatic |
| Event store | Stateful SSE with replay (3600s TTL) | `--http-stateless`, `--http-json-response` |