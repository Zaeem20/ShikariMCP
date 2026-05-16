# ShikariMCP Production Readiness Plan

Date: 2026-04-29

## Goal

Make ShikariMCP a production-grade bridge between LLM systems and real security tooling. The target is not "many wrappers"; the target is:

- every exposed tool is installable, discoverable, policy-controlled, and tested;
- every default workflow returns structured evidence an AI system can reason over;
- every dangerous action is scoped, audited, and approval-gated;
- bash and Docker installs reproduce the same verified toolset;
- generated compatibility wrappers never appear as real product functionality until verified.

## Research Anchors

The plan is based on current public docs and usage patterns from:

- MCP authorization and security guidance: [MCP Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization), [MCP Security Best Practices](https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices)
- FastMCP auth guidance: [FastMCP token verification](https://fastmcp.wiki/en/servers/auth/token-verification)
- AI agent security guidance: [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/), [OWASP LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- Comparable tools: [HexStrike AI](https://github.com/0x4m4/hexstrike-ai), [HexStrike MCP Directory](https://mcp.directory/servers/hexstrike-ai), [Strix docs](https://docs.strix.ai/), [Shannon](https://github.com/KeygraphHQ/shannon), [Shannon configuration docs](https://docs.shannon.run/en/quickstart/configuration), [Penligent MCP security article](https://penligent.ai/resources/blog/mcp-and-ai-agents-could-they-be-enterprise-security-weak-spots-the-case-for-continuous-penetration-testing)
- Tool usage docs: [Nmap XML output](https://nmap.org/book/output-formats-xml-output.html), [Nmap output flags](https://nmap.org/book/output-formats-commandline-flags.html), [Nuclei install](https://docs.projectdiscovery.io/tools/nuclei/install), [Nuclei running/output](https://docs.projectdiscovery.io/tools/nuclei/running), [Subfinder install](https://docs.projectdiscovery.io/opensource/subfinder/install), [Subfinder usage](https://docs.projectdiscovery.io/opensource/subfinder/usage), [httpx usage](https://docs.projectdiscovery.io/tools/httpx/usage), [Naabu usage](https://docs.projectdiscovery.io/opensource/naabu/usage), [Katana usage](https://docs.projectdiscovery.io/opensource/katana/usage), [ffuf output](https://github.com/ffuf/ffuf/wiki), [sqlmap usage](https://github.com/sqlmapproject/sqlmap/wiki/usage), [Trivy install](https://trivy.dev/docs/latest/getting-started/installation/), [Trivy reporting](https://trivy.dev/docs/v0.59/configuration/reporting/), [Gobuster README](https://github.com/OJ/gobuster), [Nikto export formats](https://github.com/sullo/nikto/wiki/Export-Formats)

## Current Reality

Shikari is now a safer baseline, but it is not production complete.

Already improved:

- HTTP auth fails closed unless explicitly disabled.
- HTTP host defaults to localhost in runtime config.
- generated wrappers are disabled by default.
- tool dependency metadata is tracked.
- duplicate tool names are aliased instead of silently overwritten.
- executor avoids shell execution and supports stdin, output caps, concurrency, and audit hooks.
- key workflows are more real than before.

Still blocking production:

- `pyproject.toml`, Docker, and some docs still carry old claims/defaults.
- many `auto_generated_*.py` wrappers still exist as source noise.
- default tools are not backed by a manifest with tested command templates.
- outputs are still too raw for strong AI reasoning.
- many agents are generic plan runners, not expert workflows.
- Docker and install scripts are not pinned, validated, or profile-based.
- HTTP auth is not enterprise-grade OAuth/JWT/introspection.
- approvals, RBAC, target allowlists, and rate budgets are not complete.

## Production Definition of Done

Shikari is production ready only when all of these are true:

1. `shikari_status` reports zero exposed broken tools in default mode.
2. Every exposed tool has a manifest entry, version check, install method, command schema, parser, tests, and safety policy.
3. Default HTTP cannot start without auth, and production auth supports JWT or token introspection.
4. Dangerous tools require explicit scope, target allowlist, and approval.
5. Bash installer can install and verify the default tool profile on a fresh Ubuntu/Debian host.
6. Docker image can build reproducibly and pass tool health checks.
7. Workflows return structured JSON evidence plus short human summaries.
8. Agents can plan, execute, retry, and report without hallucinating capabilities.
9. CI runs unit, integration, parser fixture, Docker build, and smoke tests.
10. README claims match measured tool health.

## Architecture Target

### 1. Verified Tool Manifest

Create a manifest-driven tool layer:

```text
manifests/
  tools/
    recon.yml
    web.yml
    vuln.yml
    cloud.yml
    forensics.yml
    passwords.yml
  installs/
    linux-apt.yml
    go-tools.yml
    python-tools.yml
    docker-tools.yml
```

Each tool entry must include:

```yaml
id: nmap_scan
display_name: Nmap Scan
binary: nmap
version_command: ["nmap", "--version"]
install:
  apt: ["nmap"]
  docker: true
profile: core
category: reconnaissance
quality: verified
scope: local
capabilities: ["active_network"]
approval: required_for_remote
target_types: ["host", "cidr", "ip"]
input_schema: shikari.schemas.NmapScanInput
command_templates:
  safe:
    argv: ["nmap", "-oX", "-", "-sV", "--version-light", "--reason", "{target}"]
    timeout: 300
parser: shikari.parsers.nmap.parse_xml
artifacts:
  machine_output: xml
tests:
  fixture: tests/fixtures/nmap/scanme.xml
```

Rules:

- Registry loads tools from manifests, not scattered decorator truth.
- Decorators can stay, but they must reference a manifest id.
- `auto_generated_*.py` files must be excluded from production packages until promoted.
- Generated wrappers can exist in a separate `experimental` package with a big opt-in flag.

### 2. Tool Runtime Contract

Every tool returns the same shape:

```json
{
  "run_id": "uuid",
  "tool": "nmap_scan",
  "status": "success|partial|failed|blocked",
  "started_at": "...",
  "duration_ms": 1234,
  "target": {"type": "host", "value": "example.com"},
  "command": {"argv": ["nmap", "..."], "redacted": false},
  "findings": [],
  "assets": [],
  "artifacts": [],
  "raw_output_ref": "artifact://...",
  "errors": [],
  "next_suggestions": []
}
```

This gives AI systems stable evidence instead of raw terminal text.

### 3. Policy Engine

Add a real policy layer before execution:

- target allowlists: domains, CIDRs, repo paths, local files;
- deny lists: cloud metadata IPs, localhost remote misuse, private ranges unless local mode;
- capability gates: `active_network`, `credential_attack`, `exploitation`, `post_exploitation`, `cloud_mutation`;
- approval modes: `never`, `local_only`, `approval_required`, `disabled`;
- rate budgets: per tool, per target, per user, per workflow;
- audit: immutable JSONL now, optional SQLite/Postgres later;
- dry-run: show exact planned commands and risk classification.

Policy decisions should be visible to the LLM through a safe `shikari_policy_explain` tool.

### 4. Auth and Deployment

Keep static bearer tokens only for local/dev.

Production HTTP should support:

- OAuth 2.1 compatible protected resource metadata;
- JWT verification through JWKS;
- OAuth token introspection for opaque enterprise tokens;
- scopes such as `shikari:read`, `shikari:run:passive`, `shikari:run:active`, `shikari:approve`, `shikari:admin`;
- per-user audit identity;
- reverse proxy examples for TLS.

FastMCP token verification docs describe static tokens as development/testing oriented, while JWT/introspection are better production paths.

### 5. AI-Native Interface

Expose fewer, better MCP surfaces:

Tools:

- `shikari_status`
- `shikari_list_tools`
- `shikari_explain_tool`
- `shikari_plan_workflow`
- `shikari_run_tool`
- `shikari_run_workflow`
- `shikari_get_artifact`
- `shikari_approve_run`
- `shikari_cancel_run`

Resources:

- `shikari://tools/catalog`
- `shikari://tools/health`
- `shikari://policy/current`
- `shikari://workflows/playbooks`
- `shikari://runs/{run_id}`

Prompts:

- `authorized_recon`
- `bug_bounty_triage`
- `web_app_assessment`
- `network_assessment`
- `cloud_config_review`
- `incident_triage`
- `report_from_evidence`

Tool descriptions must be short, factual, and free from hidden instructions. This reduces tool-description poisoning risk.

## Verified Tool Profiles

Do not try to make all 1200 wrappers real at once. Ship profiles.

### Profile 1: Core Recon

Target: reliable recon pipeline.

Tools:

- `nmap`: service discovery with XML parser.
- `subfinder`: passive subdomain discovery with JSONL or silent output.
- `httpx`: HTTP probing with JSONL output.
- `naabu`: port discovery with JSON lines output.
- `dnsx`: DNS enrichment if added.
- `whois`, `dig/nslookup`: lightweight domain context.
- `wafw00f`, `whatweb`: web technology and WAF detection.

Acceptance:

- `subfinder -> httpx -> nuclei` works through stdin or temp files.
- all results become `assets`, `services`, and `technologies`.
- no raw-only output in final agent report.

### Profile 2: Web App Testing

Tools:

- `nuclei`: use `-j/-jsonl`, `-omit-raw`, `-severity`, `-rl`, `-duc`.
- `katana`: use `-j/-jsonl`, scope flags, rate limits.
- `ffuf`: use `-json` for stdout JSONL or `-of json -o`.
- `gobuster`: use mode-specific commands and quiet output.
- `nikto`: use `-output` plus `-Format json/xml`.
- `sqlmap`: use `--batch`, controlled `--level`, controlled `--risk`; consider `sqlmapapi.py` for long-running scans.
- `dalfox`, `arjun`, `testssl.sh`, `sslscan` as second wave.

Acceptance:

- every tool has a safe profile and an aggressive profile.
- aggressive profile is approval-gated.
- parsers emit findings with severity, evidence, URL, parameter, template id, and remediation.

### Profile 3: Code, Cloud, and Container

Tools:

- `trivy`: image, fs, repo, config scans using `--format json`.
- `semgrep`: SARIF or JSON output.
- `gitleaks`: JSON/SARIF output.
- `checkov` or `kics`: IaC scanning.
- `prowler`: cloud audit, requires cloud credentials and strong policy gating.
- `kube-bench`: cluster benchmark checks.

Acceptance:

- local repo scans work without network attack permissions.
- cloud tools require explicit credential source and target account allowlist.
- output maps to compliance controls where possible.

### Profile 4: Local Forensics and Reverse Engineering

Tools:

- `file`, `strings`, `exiftool`, `binwalk`.
- `yara`, `volatility3`.
- `radare2` or `rizin`.
- optional Ghidra headless profile.

Acceptance:

- all tools are local-only.
- file paths are constrained to approved workspace roots.
- artifacts are stored and referenced, not pasted into context.

### Profile 5: Password and Offensive Tools

Tools:

- `john`, `hashcat`: offline cracking only by default.
- `hydra`, `medusa`: disabled by default or approval-gated.
- `metasploit`, `msfvenom`, payload tooling: local-only and approval-gated.

Acceptance:

- no online credential attack runs without explicit target allowlist and approval.
- payload generation never runs in remote mode by default.
- all reports include authorization warnings and audit references.

## Agent Redesign

Replace 50 generic agents with a smaller expert layer plus reusable skills.

Keep these as production agents first:

1. `ReconAgent`
2. `WebAppAgent`
3. `PentestAgent`
4. `BugBountyAgent`
5. `VulnerabilityManagementAgent`
6. `CloudSecurityAgent`
7. `CodeReviewAgent`
8. `ForensicsAgent`
9. `ReportAgent`
10. `DecisionEngineAgent`

All other agents should be one of:

- promoted after they get domain-specific logic and tests;
- kept as experimental;
- removed from default exposure;
- converted into playbook templates.

Agent contract:

```text
scope -> plan -> policy check -> dry run -> approval if needed -> execute -> parse -> correlate -> report
```

Agents should never fabricate findings. If a tool fails or is missing, the agent should return a degraded status with exact recovery steps.

## Bash Installer Plan

Create:

```text
scripts/
  install-tools.sh
  verify-tools.sh
  install-go-tools.sh
  install-wordlists.sh
  install-projectdiscovery.sh
  install-python-tools.sh
```

Primary command:

```bash
./scripts/install-tools.sh --profile core
./scripts/install-tools.sh --profile web
./scripts/install-tools.sh --profile full
./scripts/verify-tools.sh --profile web --json
```

Installer requirements:

- `set -euo pipefail`
- OS detection for Debian/Ubuntu first, then Kali, then best-effort macOS Homebrew.
- idempotent: repeated runs do not break the host.
- install to `/opt/shikari/bin` where possible, then symlink to `/usr/local/bin`.
- version pin file, for example `tools.lock`.
- install Go only if missing or too old for ProjectDiscovery/Gobuster requirements.
- use official install paths when available.
- verify every binary with `version_command`.
- write `tools-report.json` with installed/missing/version/path.
- never silently install heavyweight or risky tools in default profile.

Suggested default Ubuntu packages:

```text
curl wget git jq ca-certificates gnupg unzip tar build-essential python3-pip pipx
nmap whois dnsutils netcat-openbsd nikto dirb sqlmap sslscan tshark tcpdump
john hashcat hydra binwalk exiftool yara
```

Suggested Go tools:

```text
github.com/projectdiscovery/subfinder/v2/cmd/subfinder
github.com/projectdiscovery/httpx/cmd/httpx
github.com/projectdiscovery/nuclei/v3/cmd/nuclei
github.com/projectdiscovery/naabu/v2/cmd/naabu
github.com/projectdiscovery/katana/cmd/katana
github.com/ffuf/ffuf/v2
github.com/OJ/gobuster/v3
```

Suggested external official installers:

- Trivy through the official Aqua repository or official install script.
- Nuclei templates through `nuclei -update-templates` during verify, optional offline cache later.
- SecLists installed into `/opt/shikari/wordlists/SecLists`, optional because it is large.

## Docker Plan

Create profile-based images:

```text
docker/Dockerfile.base
docker/Dockerfile.web
docker/Dockerfile.full
docker/Dockerfile.local-privileged
```

Image rules:

- use pinned tool versions through build args and `tools.lock`;
- non-root default user;
- no default `SHIKARI_API_KEY=changeme`;
- HTTP container should require an API key at runtime;
- default host can be `0.0.0.0` inside Docker only if auth is required and documented;
- split privileged network tools into an explicit local/privileged profile;
- healthcheck should not depend on unauthenticated HTTP unless there is a separate local process health command;
- publish `shikari tools verify --json` as the image smoke test.

Compose profiles:

```yaml
profiles:
  - core
  - web
  - full
  - local-privileged
```

Security:

- default cap drop all;
- add `NET_RAW` only for profiles that need it;
- avoid `NET_ADMIN` unless a specific tool requires it;
- read-only root filesystem where possible;
- writable volumes only for audit, artifacts, templates, and cache.

## Parser and Evidence Plan

Implement parsers in:

```text
src/shikari/parsers/
  nmap.py
  nuclei.py
  subfinder.py
  httpx.py
  naabu.py
  katana.py
  ffuf.py
  nikto.py
  sqlmap.py
  trivy.py
  semgrep.py
```

Use official machine-readable formats:

- Nmap: XML via `-oX -`.
- Nuclei: JSONL via `-j/-jsonl`, omit raw by default.
- httpx: JSONL via `-j/-json`.
- Subfinder: JSONL via `-oJ` or plain silent output where sources are not needed.
- Naabu: JSON lines via `-j`.
- Katana: JSONL via `-j/-jsonl`.
- ffuf: JSON output or JSONL stdout.
- Nikto: JSON or XML through `-Format`.
- sqlmap: controlled batch output, output directory parsing, or REST JSON API for long jobs.
- Trivy: JSON via `--format json`.

Normalized models:

- `Asset`
- `Service`
- `Endpoint`
- `Technology`
- `Finding`
- `CredentialFinding`
- `SecretFinding`
- `Evidence`
- `Artifact`
- `Recommendation`

## Test Plan

Tests must cover:

- manifest schema validation;
- command builder for every verified tool;
- parser fixture tests with real sample outputs;
- missing binary behavior;
- dependency strict mode;
- remote active-tool blocking;
- approval-required behavior;
- target allowlist and denylist;
- audit log creation;
- Docker build smoke;
- installer dry-run and verify output;
- end-to-end workflows with fake binaries.

CI matrix:

- Python 3.11, 3.12, 3.13
- Windows for executor behavior
- Ubuntu for installer and integration tests
- Docker build for base and web images

## Milestones

### Milestone 0: Truth and Packaging Cleanup

Time: 1 to 2 days

- Update `pyproject.toml` description away from "1000+ tools".
- Fix Docker defaults and compose API key behavior.
- Add `.gitignore` for `.tmp`, `.shikari`, `__pycache__`, `.pytest_cache`, artifact dirs.
- Add this plan to README as the production roadmap.

Exit criteria:

- no stale "1000+ production tools" claims;
- Docker cannot start insecurely by accident;
- clean git status after generated artifacts are ignored.

### Milestone 1: Manifest Runtime

Time: 4 to 7 days

- Add manifest schema and loader.
- Convert registry to expose only manifest-verified tools by default.
- Add `shikari_list_tools` and `shikari_explain_tool`.
- Add `shikari tools verify --json` CLI path.

Exit criteria:

- `shikari_status` and manifest counts match;
- generated wrappers cannot leak into default MCP registration.

### Milestone 2: Core Tool Profile

Time: 1 to 2 weeks

- Verify Nmap, Subfinder, httpx, Naabu, Nuclei, Katana, ffuf, Gobuster, Nikto, SQLMap, Trivy.
- Implement parsers and fixtures.
- Add safe command templates and aggressive gated templates.

Exit criteria:

- core/web profile works on fresh Docker image;
- every default tool has parser tests.

### Milestone 3: Installer and Docker

Time: 1 week

- Build `scripts/install-tools.sh`.
- Build `scripts/verify-tools.sh`.
- Add Docker profile images.
- Add `tools.lock`.

Exit criteria:

- fresh Ubuntu install can run `verify-tools --profile web`;
- Docker image passes `shikari tools verify --profile web`.

### Milestone 4: AI-First Workflows

Time: 1 to 2 weeks

- Rewrite production agents around structured run results.
- Add playbooks for recon, web app, bug bounty, vuln management, cloud config, and report generation.
- Add retry/degradation logic.

Exit criteria:

- agents produce evidence-backed reports;
- no mock or fabricated finding paths in production agents.

### Milestone 5: Enterprise Controls

Time: 2 to 3 weeks

- JWT/JWKS and token introspection auth.
- RBAC and scopes.
- target allowlist/denylist.
- approval workflow.
- audit viewer/export.
- rate budgets and cancellation.

Exit criteria:

- remote HTTP deployment is defensible for a real team;
- dangerous workflows cannot run without policy and approval.

### Milestone 6: Release Hardening

Time: 1 week

- CI matrix.
- Docker signing/SBOM.
- docs for installation, auth, tool profiles, policy, examples.
- example MCP client configs.
- sample reports.

Exit criteria:

- release candidate can be installed, verified, scanned, and documented end-to-end.

## Priority Backlog

P0:

- fix Docker/compose unsafe defaults;
- add `.gitignore`;
- fix `pyproject.toml` claim;
- create manifest schema;
- expose verified manifest tools only.

P1:

- implement Nmap, Nuclei, httpx, Subfinder, Naabu, Katana parsers;
- implement installer profile `core`;
- implement Docker image `base`;
- implement `shikari_list_tools` and `shikari_run_tool`.

P2:

- web profile tools and parsers;
- approval gate;
- target allowlist;
- workflow dry-run.

P3:

- cloud/code profiles;
- OAuth/JWT/introspection;
- RBAC;
- reporting engine.

P4:

- promote or delete generated wrappers;
- plugin SDK for third-party tool packs;
- benchmark against HexStrike-style workflows and Strix/Shannon-style validated findings.

## What "Better Than Others" Means

Shikari should compete on correctness and AI usability:

- broader than Strix/Shannon as a general MCP tool bridge;
- safer than local-only offensive MCP projects by default;
- more honest than inflated wrapper-count projects;
- more useful to LLMs because outputs are structured, not terminal dumps;
- easier to deploy because install scripts and Docker profiles are first-class;
- easier to govern because policy, approvals, auth, and audit are built in.

## Immediate Next Implementation Sequence

1. Clean packaging and Docker defaults.
2. Add `.gitignore`.
3. Add manifest schema and `manifests/tools/core.yml`.
4. Convert 10 tools to manifest-backed verified tools.
5. Add parser package and fixtures.
6. Add `scripts/install-tools.sh --profile core`.
7. Add `scripts/verify-tools.sh --profile core --json`.
8. Add Docker base image using the same manifest.
9. Rewrite `ReconAgent`, `WebAppAgent`, `PentestAgent`, and `BugBountyAgent` to consume structured results only.
10. Add policy approvals and target allowlists.

