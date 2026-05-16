<p align="center">
  <img src="https://img.shields.io/badge/Tools-Verified%20First-blueviolet?style=for-the-badge&logo=hackthebox&logoColor=white" alt="Tools" />
  <img src="https://img.shields.io/badge/AI%20Agents-50-ff6600?style=for-the-badge&logo=openai&logoColor=white" alt="Agents" />
  <img src="https://img.shields.io/badge/Transport-stdio%20%2B%20HTTP-00bcd4?style=for-the-badge&logo=fastapi&logoColor=white" alt="Transport" />
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">🗡️ ShikariMCP</h1>

<p align="center">
  <strong>AI-Powered MCP Server for Ethical Hackers & Penetration Testers</strong><br/>
  <em>Verified security tools by default • 50 AI subagents • Dual transport (stdio + Streamable HTTP) • Scope-aware execution</em>
</p>

---

## What is ShikariMCP?

**ShikariMCP** is a comprehensive [Model Context Protocol (MCP)](https://spec.modelcontextprotocol.io/) server that exposes verified security tools and specialized AI subagents to any MCP-compatible client — Claude Desktop, Cursor, VS Code Copilot, and more.

It transforms your AI assistant into a **full-stack cybersecurity powerhouse** — from reconnaissance to exploitation, forensics to compliance auditing, and everything in between.

> **Shikari** (शिकारी) means "hunter" in Hindi/Urdu — because that's exactly what penetration testers are.

### Key Features

| Feature | Description |
|---------|-------------|
| 🛠️ **Verified-first Tooling** | Real wrappers are exposed by default; generated/experimental wrappers stay hidden unless explicitly enabled |
| 🤖 **50 AI Agents** | Autonomous workflow agents that chain tools together intelligently |
| 🔌 **Dual Transport** | `stdio` for local use, `Streamable HTTP` for authenticated HTTP deployment |
| 🎯 **Scope-Aware** | Tools tagged as `LOCAL`, `REMOTE`, or `BOTH` — automatically filtered by deployment context |
| 🔐 **Fail-Closed HTTP Auth** | Bearer token authentication is required for HTTP unless you explicitly opt out for development |
| 📦 **Auto-Discovery** | Drop a tool module in the right directory → it's automatically registered |
| 🐳 **Docker Ready** | Ship it anywhere with the included Dockerfile & docker-compose |

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **uv** (recommended) or pip
- Security tools you want to use must be installed on the system (Nmap, SQLMap, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/Zaeem20/ShikariMCP.git
cd ShikariMCP

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Run — stdio (Local AI Clients)

```bash
# Start in stdio mode (default) — for Claude Desktop, Cursor, etc.
shikari

# Or explicitly
shikari --transport stdio
```

### Run — HTTP (Cloud / Remote)

```bash
# Start with HTTP transport
shikari --transport http --port 8080 --api-key your-secret-key

# HTTP on your own machine (unlocks LOCAL tools)
shikari --transport http --port 8080 --api-key your-key --local
```

### Run — Docker

```bash
# Build and run
docker compose up -d

# Or build manually
docker build -t shikari -f docker/Dockerfile .
docker run -p 8080:8080 -e SHIKARI_API_KEY=your-key shikari
```

---

## Client Configuration

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "shikari": {
      "command": "shikari",
      "args": ["--transport", "stdio"]
    }
  }
}
```

### Cursor / VS Code

Add to `.cursor/mcp.json` or equivalent:

```json
{
  "mcpServers": {
    "shikari": {
      "command": "shikari",
      "args": ["--transport", "stdio"]
    }
  }
}
```

### Remote HTTP Client

```json
{
  "mcpServers": {
    "shikari": {
      "url": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

---

## Architecture

```
ShikariMCP/
├── src/shikari/
│   ├── server.py              # Main MCP server (dual transport)
│   ├── config.py              # Configuration management
│   │
│   ├── core/
│   │   ├── registry.py        # Tool auto-discovery & scope filtering
│   │   ├── executor.py        # Safe subprocess execution with timeout
│   │   ├── auth.py            # API key authentication middleware
│   │   ├── validator.py       # Input sanitization
│   │   └── result_parser.py   # Output parsing utilities
│   │
│   ├── agents/                # 50 AI Subagents
│   │   ├── _base_agent.py     # Base agent class (plan→execute→analyze→report)
│   │   ├── workflow/          # 12 end-to-end workflow agents
│   │   ├── intelligence/      # 10 analysis & intelligence agents
│   │   ├── infrastructure/    # 8 system & optimization agents
│   │   ├── domain/            # 10 domain-specific agents
│   │   ├── offensive/         # 5 attack-phase agents
│   │   └── defensive/         # 5 blue team & forensics agents
│   │
│   └── tools/                 # Verified tools + opt-in generated catalog
│       ├── _base.py           # @shikari_tool decorator & ToolScope
│       ├── reconnaissance/    # Nmap, Masscan, Subfinder, Amass, etc.
│       ├── enumeration/       # SMB, SNMP, AD, service enumeration
│       ├── vulnerability_scanning/  # Nuclei, Nikto, OpenVAS, etc.
│       ├── web_application/   # SQLMap, XSStrike, Burp, FFUF, etc.
│       ├── exploitation/      # Metasploit, SearchSploit, exploit tools
│       ├── post_exploitation/ # Mimikatz, LinPEAS, persistence, C2
│       ├── password_attacks/  # Hashcat, John, Hydra, CeWL, etc.
│       ├── wireless/          # Aircrack-ng, Reaver, Bettercap
│       ├── reverse_engineering/ # Ghidra, Radare2, Binary Ninja
│       ├── forensics/         # Volatility, Autopsy, Binwalk
│       ├── cloud_security/    # ScoutSuite, Prowler, CloudSploit
│       ├── container_security/ # Trivy, Falco, kube-bench
│       ├── osint/             # TheHarvester, Maltego, Sherlock
│       ├── network_attacks/   # Responder, Bettercap, Ettercap
│       ├── mobile_security/   # Frida, Objection, APKTool
│       ├── iot_security/      # Firmware analysis, protocol tools
│       ├── cryptography/      # Encryption, hash analysis, attacks
│       ├── evasion/           # AV bypass, WAF bypass, obfuscation
│       ├── payload_generation/ # msfvenom, shellcode, crafting
│       ├── reporting/         # Report generators, data processing
│       └── ...                # And more categories
│
├── tests/                     # Pytest test suite
├── docker/                    # Dockerfile & docker-compose.yml
└── pyproject.toml
```

---

## Tool Catalog Health

ShikariMCP keeps the broad catalog for compatibility, but it exposes only verified wrappers by default. Generated wrappers are disabled unless you explicitly opt in with `SHIKARI_ENABLE_GENERATED_TOOLS=true`; catalog-only experimental agents are disabled unless `SHIKARI_ENABLE_EXPERIMENTAL_TOOLS=true`.

Use `shikari_status` for exact runtime counts on your machine. Availability depends on transport, enabled safety gates, and which external binaries are installed.

| Surface | Default | Notes |
|---------|---------|-------|
| Verified wrappers | Exposed | Manual wrappers and production workflow tools |
| Manifest-backed tools | Exposed through `shikari_*` catalog/run tools | Best path for AI clients because outputs are normalized |
| Generated wrappers | Hidden | Compatibility catalog, not advertised as production-ready |
| Catalog-only agents | Hidden | Opt-in as experimental until they have domain-specific execution logic |

| # | Category | Registered | Description |
|---|----------|-----------:|-------------|
| 1 | **Reconnaissance** | 65 | Passive/active recon, subdomain enum, DNS, port scanning |
| 2 | **Enumeration** | 30 | Network, web, SMB, AD, SNMP, service enumeration |
| 3 | **Vulnerability Scanning** | 193 | Network, web, CMS, SSL/TLS scanners |
| 4 | **Web Application** | 259 | SQLi, XSS, fuzzing, API testing, auth bypass, CMS checks |
| 5 | **Exploitation** | 158 | Exploit frameworks and validation tools |
| 6 | **Post-Exploitation** | 155 | Privilege escalation, lateral movement, persistence, C2 catalog entries |
| 7 | **Password Attacks** | 108 | Hashcat, John, brute force, wordlist tools |
| 8 | **Network Attacks** | 64 | Sniffing, MITM, spoofing, DoS catalog entries |
| 9 | **OSINT** | 63 | People search, domain intel, social media, breach detection |
| 10 | **Mobile** | 52 | Android, iOS, mobile analysis and forensics |
| 11 | **Cloud Security** | 5 | AWS, Azure, GCP, multi-cloud security |
| 12 | **Forensics** | 4 | Memory, disk, network forensics, steganography |
| 13 | **Wireless** | 3 | WiFi, Bluetooth, RF tools |
| 14 | **Reverse Engineering** | 3 | Disassemblers, debuggers, binary analysis |
| 15 | **Evasion & Payloads** | 4 | AV evasion, WAF bypass, payload generation |
| 16 | **Database** | 2 | SQL/NoSQL injection checks |
| 17 | **Agents** | 50 | Workflow, domain, intelligence, defensive, offensive, and infrastructure agents |

### Currently Supported Integrations

The production path is manifest-backed. These are the integrations Shikari currently treats as the **core supported tool profile**. They are listed in `src/shikari/manifests/tools/core.json`, can be checked with `shikari tools verify --profile core --json`, and are the first tools targeted by the installer and Docker image.

| Tool | Shikari ID | Category | What Shikari uses it for | Output target | Install source |
|------|------------|----------|---------------------------|---------------|----------------|
| **Nmap** | `nmap_scan` | Reconnaissance | Service/version discovery, host and CIDR scanning | XML | `apt: nmap` |
| **Subfinder** | `subfinder_enum` | Reconnaissance | Passive subdomain enumeration | JSONL | Go install |
| **httpx** | `httpx_probe` | Reconnaissance | HTTP probing, status, title, tech detection, response metadata | JSONL | Go install |
| **Nuclei** | `nuclei_scan` | Vulnerability scanning | Template-based vulnerability checks with rate-limited safe defaults | JSONL | Go install |
| **Naabu** | `naabu_scan` | Reconnaissance | Fast port discovery before deeper probing | JSONL | Go install + `libpcap` |
| **Katana** | `katana_crawl` | Web application | Crawling and endpoint discovery | JSONL | Go install |
| **ffuf** | `ffuf_fuzz` | Web application | Directory/content fuzzing with controlled rate | JSON/JSONL | Go install |
| **Gobuster** | `gobuster_dir` | Web application | Directory brute forcing when ffuf is not preferred | Text | Go install |
| **Nikto** | `nikto_scan` | Web application | Web server misconfiguration and known issue checks | JSON | `apt: nikto` |
| **SQLMap** | `sqlmap_scan` | Web application | Conservative SQL injection testing with `--batch --level 1 --risk 1` | Text | `apt: sqlmap` |
| **Trivy** | `trivy_scan` | Cloud/container/code security | Filesystem, image, repository, dependency, and config scanning | JSON | Official Trivy installer |
| **Whois** | `whois_lookup` | Reconnaissance | Domain/IP registration context | Text | `apt: whois` |

The broader default registry also includes manual wrappers for tools such as `masscan`, `hashcat`, `john`, `hydra`, `sslscan`, `sslyze`, `binwalk`, `exiftool`, `aircrack-ng`, `tshark`, `tcpdump`, and workflow agents. Those wrappers are available through normal MCP discovery, but the table above is the current **manifest-verified** support set.

Generated compatibility wrappers are still present in the repository, but they are disabled by default and should not be treated as supported production integrations until promoted into a manifest profile.

### Supported Profiles

| Profile | Purpose | Additional integrations |
|---------|---------|-------------------------|
| `core` | Default local-first recon, probing, web scan, container/code scan | Nmap, Subfinder, httpx, Nuclei, Naabu, Katana, ffuf, Gobuster, Nikto, SQLMap, Trivy, Whois |
| `recon` | Asset discovery and target normalization | Masscan, dnsx, mapcidr, uncover |
| `web` | Web application testing extras | WhatWeb, wafw00f, testssl.sh, Dalfox, Arjun, SSLScan, tlsx |
| `cloud` | Code, secrets, IaC, and container security | Semgrep, Gitleaks, Checkov |
| `forensics` | Local analysis and reverse engineering | YARA, Volatility3, Radare2 |
| `offensive` | Explicit opt-in offline/credential testing | John, Hashcat, Hydra |
| `full` | Combined workstation arsenal | Aggregates all profiles |

### Install and Verify Tools

For Debian/Ubuntu/Kali-style systems:

```bash
# Install the supported core profile
./scripts/install-tools.sh --profile core

# Verify installed binaries and versions
./scripts/verify-tools.sh --profile core --json

# Or use the Python CLI directly
shikari tools verify --profile core --json

# Explain or preview a verified command before running it
shikari tools explain nmap_scan
shikari tools dry-run nmap_scan --input target=scanme.nmap.org
```

The installer is intentionally conservative: it installs the supported core profile, not every experimental wrapper in the repository.

---

## AI Subagents (50)

Every agent follows a structured **plan → execute → analyze → report** workflow. Each is exposed as an MCP tool that can be invoked by your AI client.

### 🔄 Workflow Agents (13)

| Agent | Audience | What it does |
|-------|----------|-------------|
| **ReconAgent** | 🔴🏴🟢 | Full recon pipeline — passive → subdomains → DNS → ports → services |
| **PentestAgent** | 🔴🟣 | Complete pentest lifecycle — recon → vuln scan → exploit → report |
| **BugBountyAgent** | 🏴 | Bug bounty pipeline — subdomain → fuzzing → param mining → injection |
| **WebAppWorkflowAgent** | 🏴🔴 | Web app workflow — fingerprint → probe → crawl → templates → parameters |
| **CTFAgent** | 🟢 | CTF solver — identifies challenge type → selects tools → solves |
| **RedTeamAgent** | 🔴 | Full kill chain — access → privesc → lateral → persistence → exfil |
| **BlueTeamAgent** | 🔵 | Defensive assessment — logs → detection gaps → hardening checks |
| **PurpleTeamAgent** | 🟣 | Combined red+blue — attacks AND validates detection capabilities |
| **IncidentResponseAgent** | 🔵🟣 | IR workflow — triage → containment → eradication → recovery |
| **ThreatHuntAgent** | 🔵🟣 | Proactive hunting — IOC search → behavioral analysis → YARA |
| **ComplianceAgent** | 🟡 | Compliance auditing — CIS, PCI-DSS, HIPAA, SOC2, ISO27001 |
| **VulnManagementAgent** | 🟡🔵 | Vuln lifecycle — scan → prioritize → track → verify fix |
| **CodeReviewAgent** | 🟢🏴 | Source code security — SAST → secrets → dependencies → patterns |

### 🧠 Intelligence Agents (10)

| Agent | What it does |
|-------|-------------|
| **CVEIntelAgent** | CVE lookup, exploit availability, severity scoring |
| **ExploitGenAgent** | Analyzes vulns → generates PoC exploits → tests |
| **VulnCorrelatorAgent** | Attack chain discovery — maps chained vulnerabilities |
| **ThreatIntelAgent** | OSINT, breach databases, APT TTPs, MITRE ATT&CK |
| **AttackSurfaceAgent** | Maps all external assets — subdomains, APIs, cloud |
| **ReportAgent** | Aggregates findings → executive + technical report |
| **IOCExtractorAgent** | Extracts IOCs from scan outputs → structured feeds |
| **RiskScoringAgent** | Context-aware risk scoring with business impact |
| **ZeroDayResearchAgent** | Fuzzing, crash analysis, PoC development |
| **ThreatModelingAgent** | STRIDE/DREAD threat modeling |

### ⚙️ Infrastructure Agents (8)

| Agent | What it does |
|-------|-------------|
| **DecisionEngine** | Selects optimal tool combination for given objective |
| **ParamOptimizer** | Tunes parameters based on context |
| **RateLimiter** | Detects WAFs → adjusts speed & rotates |
| **FailureRecovery** | Diagnoses failures → retries with adjusted params |
| **PerformanceMonitor** | Monitors resources → throttles if needed |
| **ResourceScheduler** | Queue prioritization & concurrent execution |
| **HealthCheckAgent** | Checks tool installations & dependencies |
| **ConfigManager** | Scan profiles & environment presets |

### 🎯 Domain-Specific Agents (10)

| Agent | What it does |
|-------|-------------|
| **WebAppAgent** | Full web app testing — spider → inject → auth bypass |
| **NetworkAgent** | Network security — discovery → scan → exploit → traffic |
| **CloudAgent** | Multi-cloud — IAM, storage, serverless, compliance |
| **MobileAgent** | Android + iOS — reversing, hooking, cert pinning |
| **OSINTAgent** | Full OSINT — people → email → social → breach → dossier |
| **ActiveDirectoryAgent** | AD attacks — Kerberoast, delegation, BloodHound |
| **MalwareAgent** | Static + dynamic analysis, IOC extraction, YARA |
| **IoTSCADAAgent** | Firmware, MQTT/CoAP/Modbus, PLC enumeration |
| **WirelessAgent** | WiFi + Bluetooth + RF analysis |
| **DatabaseAgent** | SQL/NoSQL injection, privilege escalation |

### ⚔️ Offensive Agents (5)

| Agent | What it does |
|-------|-------------|
| **PrivEscAgent** | Linux SUID/cron/kernel + Windows tokens/services/UAC |
| **LateralMovementAgent** | Pass-the-hash, PSExec, WMI, SSH pivoting, SOCKS |
| **EvasionAgent** | AV/AMSI/ETW bypass, obfuscation, process injection |
| **PayloadCraftAgent** | Shellcode, staged/stageless, multi-platform, C2 |
| **CredHarvestAgent** | Mimikatz, LSASS, SAM, Kerberos tickets, NTDS |

### 🛡️ Defensive Agents (5)

| Agent | What it does |
|-------|-------------|
| **HardeningAgent** | OS benchmarks, service minimization, firewall rules |
| **ForensicsAgent** | Memory + disk + network + log forensics |
| **MalwareTriageAgent** | Classification, hash lookup, YARA, sandbox, IOCs |
| **AnomalyDetectAgent** | Log analysis, network anomalies, behavioral alerts |
| **ContainmentAgent** | Network isolation, lockout, firewall, DNS sinkhole |

---

## Scope System

ShikariMCP uses a **scope-aware** execution model to safely handle different deployment scenarios:

```python
class ToolScope(str, Enum):
    LOCAL  = "local"   # Only via stdio or HTTP + --local
    REMOTE = "remote"  # Safe for cloud/remote deployment
    BOTH   = "both"    # Works everywhere (default)
```

| Transport | `--local` flag | LOCAL tools | REMOTE tools | BOTH tools |
|-----------|---------------|-------------|--------------|------------|
| stdio | N/A | ✅ | ✅ | ✅ |
| HTTP | **Yes** | ✅ | ✅ | ✅ |
| HTTP | **No** | ❌ Blocked | ✅ | ✅ |

> **Why `--local`?** Some users want HTTP transport for convenience (browser-based clients) but run on their own machine. Without `--local`, tools requiring physical access (network sniffers, wireless) would be blocked.

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHIKARI_TRANSPORT` | `stdio` | Transport mode (`stdio` or `streamable-http`) |
| `SHIKARI_HOST` | `127.0.0.1` | HTTP bind address |
| `SHIKARI_PORT` | `8080` | HTTP port |
| `SHIKARI_ALLOW_UNAUTHENTICATED_HTTP` | `false` | Explicit development-only opt-out for HTTP auth |
| `SHIKARI_API_KEY` | — | API key for HTTP auth (required for HTTP) |
| `SHIKARI_LOCAL_MODE` | `false` | Treat HTTP as local deployment |
| `SHIKARI_TIMEOUT` | `300` | Default tool execution timeout (seconds) |
| `SHIKARI_MAX_CONCURRENT` | `10` | Max concurrent tool executions |
| `SHIKARI_MAX_OUTPUT_CHARS` | `50000` | Per-command output cap before truncation |
| `SHIKARI_TOOL_PROFILE` | `core` | Default manifest-backed tool profile |
| `SHIKARI_ENABLE_GENERATED_TOOLS` | `false` | Expose generated compatibility wrappers |
| `SHIKARI_ENABLE_EXPERIMENTAL_TOOLS` | `false` | Expose catalog-only experimental agents/wrappers |
| `SHIKARI_REQUIRE_TOOL_DEPENDENCIES` | `false` | Hide wrappers whose binaries are not installed |
| `SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS` | `false` | Allow dangerous/active wrappers in remote HTTP mode |
| `SHIKARI_ENABLE_ACTIVE_TOOLS` | `false` | Allow manifest-backed active network/scanning tools to execute |
| `SHIKARI_ENABLE_OFFENSIVE_TOOLS` | `false` | Allow explicit offensive profile tools |
| `SHIKARI_ENABLE_CREDENTIAL_TOOLS` | `false` | Allow credential attack tools |
| `SHIKARI_TARGET_ALLOWLIST` | — | Comma-separated authorized hosts, domains, CIDRs, or filesystem roots |
| `SHIKARI_AUDIT_ENABLED` | `true` | Write JSONL tool execution audit events |
| `SHIKARI_AUDIT_LOG_PATH` | `.shikari/audit.jsonl` | Audit log path |
| `SHIKARI_LOG_LEVEL` | `INFO` | Logging level |

### CLI Flags

```bash
shikari [OPTIONS]

Options:
  --transport {stdio,http}   Transport mode (default: stdio)
  --host HOST                HTTP bind address (default: 127.0.0.1)
  --port PORT                HTTP port (default: 8080)
  --local                    Treat HTTP as local (unlock LOCAL tools)
  --api-key KEY              API key for HTTP auth
  --allow-unauthenticated-http
                              Allow HTTP without bearer auth for development
  --enable-generated-tools   Expose generated compatibility wrappers
  --enable-experimental-tools
                              Expose experimental wrappers and catalog-only agents
  --require-tool-dependencies
                              Hide wrappers whose binaries are missing
  --enable-remote-active-tools
                              Allow active/dangerous tools in remote HTTP mode
  --enable-active-tools      Allow manifest-backed active network/scanning tools
  --enable-offensive-tools   Allow explicit offensive tools
  --enable-credential-tools  Allow credential attack tools
  --target-allowlist LIST    Authorized domains, hosts, IPs, CIDRs, or paths
  --tool-profile PROFILE     Default manifest-backed profile
  --log-level LEVEL          Logging level (DEBUG/INFO/WARNING/ERROR)
```

### `.env` File

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

---

## Development

### Setup

```bash
git clone https://github.com/Zaeem20/ShikariMCP.git
cd ShikariMCP
uv sync --group dev
```

### Adding a New Tool

1. Create or edit a file in the appropriate `src/shikari/tools/<category>/` directory
2. Use the `@shikari_tool` decorator:

```python
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="my_tool",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="mytool",
    description="Description of what the tool does"
)
async def my_tool(target: str, extra_args: str = "") -> str:
    """
    Run mytool against a target.

    Args:
        target: Target host/domain
        extra_args: Additional CLI flags
    """
    cmd = ["mytool", target]
    result = await execute_command(cmd, timeout=300)
    return result.output
```

3. That's it! The auto-discovery system will pick it up on the next server restart.

### Adding a New Agent

1. Create a file in `src/shikari/agents/<category>/`
2. Extend `BaseAgent` and implement `plan()` and `execute()`
3. Expose it as an MCP tool with `@shikari_tool`

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test
uv run pytest tests/test_server.py -v

# With coverage
uv run pytest tests/ -v --cov=shikari
```

---

## Docker

### Build

```bash
docker build -t shikari -f docker/Dockerfile .
```

### Smoke Test

```bash
# Base image should build and verify the core profile during the build.
docker build -t shikari:smoke -f docker/Dockerfile .

# Optional profile layers after the base image exists.
docker build -t shikari:web -f docker/Dockerfile.web .
docker build -t shikari:full -f docker/Dockerfile.full .
```

### Run

```bash
# HTTP mode; provide a real key
docker run -p 8080:8080 \
  -e SHIKARI_API_KEY=your-secret-key \
  shikari

# With docker-compose
export SHIKARI_API_KEY=your-secret-key
docker compose up -d
```

### Include Security Tools

The Docker image includes the supported core profile tools listed above, plus common local utilities used by existing wrappers. To add more, extend the Dockerfile or add a new manifest profile:

```dockerfile
RUN apt-get update && apt-get install -y your-tool-here
```

---

## Audience

ShikariMCP is built for **every cybersecurity professional**:

| Role | Key Agents & Tools |
|------|-------------------|
| 🔴 **Red Team** | RedTeamAgent, PrivEscAgent, EvasionAgent, exploitation tools |
| 🔵 **Blue Team** | BlueTeamAgent, ForensicsAgent, HardeningAgent, detection tools |
| 🟣 **Purple Team** | PurpleTeamAgent, ThreatHuntAgent, combined red+blue workflows |
| 🟢 **Security Researcher** | CTFAgent, ZeroDayResearchAgent, reverse engineering tools |
| 🏴 **Bug Bounty Hunter** | BugBountyAgent, WebAppAgent, recon & injection tools |
| 🟡 **GRC / Compliance** | ComplianceAgent, RiskScoringAgent, audit & benchmark tools |
| 🔍 **SOC Analyst** | IncidentResponseAgent, IOCExtractorAgent, forensics tools |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Add your tool/agent following the patterns above
4. Write tests for your additions
5. Submit a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

> ⚠️ **ShikariMCP is designed for authorized security testing only.** Always obtain proper written authorization before testing any systems you do not own. The authors are not responsible for misuse of this software. Use responsibly and ethically.

---

<p align="center">
  <strong>Built with ❤️ for the cybersecurity community</strong><br/>
  <em>🗡️ Hunt smart. Hunt ethically. Hunt with ShikariMCP.</em>
</p>
