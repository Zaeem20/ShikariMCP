# ShikariMCP Security Tooling Review

Initial review date: 2026-04-25
Remediation pass: 2026-04-29

## Remediation status

The findings below describe the pre-hardening state. The implementation has since been updated to make the product safer and more honest by default:

| Area | Previous risk | Current status |
|---|---|---|
| HTTP exposure | HTTP could start unauthenticated on `0.0.0.0` | Defaults to `127.0.0.1` and refuses unauthenticated HTTP unless `--allow-unauthenticated-http` or `SHIKARI_ALLOW_UNAUTHENTICATED_HTTP=true` is explicitly set |
| Tool claim | The product implied all 1200+ wrappers were production tools | README now advertises verified-first behavior: 213 verified/default wrappers, 1005 generated wrappers disabled by default, 1218 total registered wrappers |
| Generated/no-op wrappers | Generated compatibility wrappers were exposed like real tools | Generated wrappers are hidden unless `SHIKARI_ENABLE_GENERATED_TOOLS=true` |
| Dependency health | `requires_binaries` metadata was ignored | Tool metadata now stores dependency requirements and reports missing binaries through `shikari_status`; strict blocking is available with `SHIKARI_REQUIRE_TOOL_DEPENDENCIES=true` |
| Command execution | No stdin support, weak output control, no audit trail | Executor now uses argument-list subprocess execution, stdin support, concurrency limits, output truncation, and JSONL audit events |
| Duplicate tools | Later duplicate names silently overwrote earlier wrappers | Duplicates are preserved with category-prefixed aliases and reported in tool health |
| Remote dangerous tools | Many active/offensive tools could appear in remote HTTP mode | Dangerous generated/active tools are blocked remotely unless explicitly enabled |
| Agents | Many agents returned mocked/no-op results | Generic agents now produce executable conservative plans; Recon, Pentest, Bug Bounty, and Red Team workflows were replaced with safer real-tool orchestration or explicit approval/runbook output |
| Tests | Baseline behavior did not cover the hardened defaults | Test suite updated; `55 passed` on the Windows project environment |

Remaining production work: add JWT/OAuth or token introspection for multi-user deployments, approvals/RBAC for dangerous tools, structured parsers for more tools, CI integration, signed tool manifests, and end-to-end HTTP auth tests behind a reverse proxy/TLS deployment guide.

## Initial executive verdict

ShikariMCP is directionally right in one important way: adding HTTP transport to a HexStrike-inspired security MCP server is a valid product gap, and the current FastMCP `streamable-http` integration is a reasonable starting point. The implementation is not yet production-right. It currently behaves more like a large proof-of-concept scaffold than a dependable security automation platform.

The main strength is breadth of intent: dual transport, scope filtering, a decorator registry, Docker packaging, and a lot of common tool categories. The main weakness is trustworthiness: 1005 of 1169 tool wrappers under `src/shikari/tools` are auto-generated placeholders, many commands do not map to real binaries, many agents are mocked/no-op, auth can be disabled in HTTP mode, tool dependencies are not enforced, and several wrappers use command patterns that will not work with the current executor.

My practical rating:

| Area | Current state | Risk |
|---|---:|---:|
| HTTP transport concept | Good start | Medium |
| HTTP production security | Incomplete | High |
| Tool coverage claim | Overstated | High |
| Real tool usability | Mixed | High |
| Agent workflows | Mostly scaffolded | High |
| Code maintainability | Simple but inconsistent | Medium |
| Broken functionality probability | High | High |
| Competitive readiness | Not yet | High |

## Sources reviewed

External references:

- [HexStrike AI GitHub](https://github.com/0x4m4/hexstrike-ai) and [MCP.Directory listing](https://mcp.directory/servers/hexstrike-ai): public docs describe 150+ security tools, 12+ autonomous agents, and local stdio usage.
- [DMontgomery40/pentest-mcp GitHub](https://github.com/DMontgomery40/pentest-mcp): docs describe stdio, HTTP streaming, legacy SSE, OAuth 2.1, Docker, and a smaller set of concrete tools such as Nmap, Gobuster, Nikto, John, and Hashcat.
- [Penligent MCP/AI-agent security article](https://penligent.ai/resources/blog/mcp-and-ai-agents-could-they-be-enterprise-security-weak-spots-the-case-for-continuous-penetration-testing): highlights MCP risks around privileged tools, prompt/tool misuse, auditing, policy, and continuous testing.
- [Penligent automated pentesting overview](https://penligent.ai/resources/blog/overview-of-penligentais-automated-penetration-testing-tool): positions Penligent as end-to-end AI pentesting with attack chains, reporting, CI/CD, and compliance.
- [KeygraphHQ Shannon GitHub](https://github.com/KeygraphHQ/shannon): autonomous white-box web/API pentester with source analysis, live exploit proof, Docker worker model, and sample benchmark/report claims.
- [Shannon configuration docs](https://docs.shannon.run/en/quickstart/configuration): documents production controls: auth, approvals, rate limits, domain allowlists, circuit breakers, observability, and sandboxing.
- [FastMCP token verification docs](https://gofastmcp.com/v2/servers/auth/token-verification): static token verification is documented as development/testing-oriented; JWT/introspection are the production path.

Local files reviewed:

- `src/shikari/server.py`
- `src/shikari/config.py`
- `src/shikari/core/auth.py`
- `src/shikari/core/executor.py`
- `src/shikari/core/registry.py`
- `src/shikari/tools/_base.py`
- representative tool modules and agents
- `docker/Dockerfile`
- test suite under `tests/`

## Competitive comparison

| Aspect | ShikariMCP | HexStrike MCP | pentest-mcp | Penligent | Shannon |
|---|---|---|---|---|---|
| Primary model | MCP wrapper suite for many security CLIs | MCP cyber automation with 150+ tools and 12+ agents | MCP toolkit with focused professional pentest tools | Enterprise AI pentesting platform/cockpit | Autonomous white-box web/API pentester |
| Transport | stdio + FastMCP streamable HTTP | Public listings emphasize local stdio | stdio + HTTP streaming + SSE | Platform/API, not just MCP wrapper | CLI/Docker worker, not primarily a general MCP security tool |
| Auth | Static bearer token if configured; HTTP can run unauthenticated | Not the main differentiator in public docs | OAuth 2.1 claimed in docs | Enterprise governance emphasis | Auth/approvals/gateway controls documented |
| Tool breadth | Claims 1200+, registry shows 1213, but 1005 generated placeholders | 150+ named security tools | Smaller curated set | Claims broad automation with classic tools | Focused tools for recon and exploit validation |
| Tool fidelity | Low-to-mixed; many placeholders like `web_application_tool_0` | Higher public credibility because docs name real tools | Higher for core tools, lower breadth | Platform-level, less inspectable from public docs | High emphasis on confirmed PoCs, but narrower scope |
| Agents | 50 registered, but 45 are generic no-op mock agents | 12+ agents, positioned as autonomous workflows | Workflow/natural language integration | Multi-agent attack-chain platform | Multi-phase exploit agents |
| Safety controls | Scope filter only; no approvals, no audit trail, no rate limiter enforcement | Has misuse concerns due power and popularity | OAuth/security options claimed | Strongly emphasizes continuous validation and governance | Approvals, auth, allowlists, budgets, rate limits in docs |
| Reporting | Basic agent report strings | Automated reports claimed | Client-ready reporting claimed | Compliance-ready reporting | Sample reports and PoC evidence are core |
| Best current use | Local experimentation and scaffold for a broader MCP suite | Local AI-assisted offensive workflows | Practical smaller MCP pentest toolkit | Enterprise AI pentest validation | Source-aware appsec validation |

## Pros of ShikariMCP

1. Dual transport is the strongest differentiator versus HexStrike.
   `server.py` creates a FastMCP server and runs HTTP with `transport="streamable-http"`, which is the right family of protocol for remote MCP usage.

2. The scope model is a good idea.
   `ToolScope.LOCAL`, `REMOTE`, and `BOTH` in `src/shikari/tools/_base.py` give you the beginning of a policy boundary between local-only tools and tools safe to expose remotely.

3. The executor uses `asyncio.create_subprocess_exec`.
   That avoids direct shell execution by default, which is much safer than `shell=True`.

4. Auto-discovery keeps extension friction low.
   A new decorated tool module can be imported and registered without editing a central list.

5. Docker packaging installs a useful real baseline.
   The Dockerfile installs Nmap, Masscan, Nikto, Dirb, John, Hashcat, Hydra, SQLMap, Aircrack, SSLScan, SSlyze, and common ProjectDiscovery tools.

6. The test suite covers basic registry, scope, executor, and server creation behavior.
   It is not enough yet, but the foundation is there.

## Cons and likely broken functionality

### 1. The "1200+ tools" claim is mostly not real yet

Measured locally:

- 1213 registered tools/agents after discovery.
- 1169 tool decorators under `src/shikari/tools`.
- 1005 of those are in `auto_generated_*.py`.
- Many auto-generated binaries are placeholders such as `web_application_tool_0`, `vulnerability_scanning_tool_0`, `password_attacks_tool_0`, etc.

This means the advertised breadth will fail in real use because those binaries do not exist. This is the biggest product credibility issue.

Recommendation: split the README count into:

- "verified tools"
- "experimental/generated wrappers"
- "planned integrations"

Do not advertise generated placeholders as working security tools.

### 2. HTTP auth exists but can be absent in the most dangerous mode

`src/shikari/core/auth.py` returns `None` if HTTP is enabled without an API key, so the server can run unauthenticated over `0.0.0.0`. `server.py` logs a warning, but still starts.

FastMCP's docs say static token verification is mainly for development/testing; production should use JWT or introspection-based verification. Shikari currently uses a static bearer token approach and has no TLS, OAuth, JWT issuer/audience validation, rate limiting, audit logs, or approval workflow.

Recommendation:

- Refuse to start HTTP unless `--api-key` is set, unless `--allow-unauthenticated-http` is explicitly passed.
- Bind to `127.0.0.1` by default.
- Add JWT/introspection auth for production.
- Add per-tool audit logging and request IDs.
- Add rate limits and approval gates for dangerous tools.

### 3. `requires_binaries` is passed but ignored

Several generated/manual wrappers pass `requires_binaries=[...]`, but `shikari_tool()` accepts `**kwargs` and discards them. `ToolMetadata` only stores `binary`, not `requires_binaries`.

Result: tools appear available even when dependencies are missing.

Recommendation:

- Store `requires_binaries`.
- Check dependencies at registration time or expose a `healthcheck_tools` report.
- Mark missing tools as unavailable or degraded.

### 4. Many wrappers use shell features that the executor cannot run

The executor uses `shlex.split()` plus `create_subprocess_exec()`. That is good for avoiding shell injection, but commands like these will not work as intended:

```python
cmd = "echo {target} | waybackurls".replace("{target}", target)
return await execute_command(cmd, timeout=300)
```

With no shell, `|` is just an argument to `echo`; `waybackurls` never runs. This affects wrappers in `enumeration/web_enum.py` and similar modules.

Recommendation:

- Use explicit subprocess pipelines where needed.
- Prefer list commands everywhere.
- For tools that require stdin, add `stdin` support to `execute_command()`.

### 5. Scope classification is too permissive

The remote HTTP mode registers 1076 of 1213 tools. Only 137 are local. Many web, enumeration, exploitation, and generated placeholder tools are marked `ToolScope.BOTH` even though they can perform active network scanning or exploitation.

This weakens the main safety boundary.

Recommendation:

- Default unknown/generated wrappers to `LOCAL`, not `BOTH`.
- Treat exploitation, brute force, MITM, wireless, cracking, payload generation, network scanning, and active fuzzing as `LOCAL` or approval-required.
- Introduce capability labels such as `network_access`, `credential_attack`, `destructive`, `file_write`, `exfiltration`, `shell`.

### 6. Agents are mostly mock/no-op

There are 50 agent tools, but 45 contain a generic pattern like:

```python
return [{"name": "analyze", "tool": "noop", "cmd": ["echo", target]}]
```

and return mocked results. `PentestAgent` also returns hard-coded findings instead of executing its plan. That is fine for a scaffold, but not for a claimed autonomous pentest platform.

Recommendation:

- Label mock agents as experimental.
- Convert agents one by one into real workflows with tool invocation, output parsing, state passing, and tests.
- Remove or hide no-op agents from production registration until implemented.

### 7. Tool output parsing is mostly absent

Most wrappers return raw stdout/stderr. Competitors like Shannon and Penligent emphasize validated findings, evidence, and reportable PoCs. Shikari currently exposes command output rather than a dependable finding model.

Recommendation:

- Add structured result schemas per tool category.
- Parse Nmap XML/JSON, Nuclei JSONL, SQLMap outputs, Nikto reports, etc.
- Store raw output plus normalized findings.

### 8. Broken tests indicate environment fragility

I ran:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests -q -s
```

Result:

- 50 passed
- 5 failed

All failures are in `tests/test_executor.py` because tests call `python`, but this Windows environment only resolved the venv interpreter path, not a `python` command on PATH. The first run also hit pytest temp/cache permission issues under sandboxed temp paths.

Recommendation:

- Use `sys.executable` in executor tests.
- Disable pytest cache in constrained runs or ensure `.pytest_cache` permissions.
- Add CI on Windows and Linux.

### 9. Duplicate tool names silently overwrite each other

Detected duplicates:

- `nmap_scan`: reconnaissance and vulnerability_scanning
- `whois_lookup`: osint and reconnaissance
- `amass_enum`: dns_enum and subdomain_enum
- `httpx_probe`: asset_discovery and subdomain_enum
- `msfvenom_generate`: evasion_payloads and payload_generation

The registry is a dict keyed by name, so later imports silently overwrite earlier tools.

Recommendation:

- Fail registration on duplicate names unless explicitly overriding.
- Namespace tools by category, e.g. `recon_nmap_scan` and `vuln_nmap_scan`.

### 10. Concurrency configuration is not enforced

`ShikariConfig.max_concurrent_tools` exists, but there is no global semaphore around tool execution. A remote user/client could start many expensive scans in parallel.

Recommendation:

- Add an async semaphore in the executor or MCP tool wrapper.
- Add queueing, cancellation, per-client limits, and timeouts per category.

## Is the HTTP implementation right?

Partly.

What is right:

- Using FastMCP is a good base.
- `streamable-http` transport is an appropriate modern MCP transport path.
- Passing an auth provider into `FastMCP(...)` is the right integration point.
- Keeping logs on stderr is correct for stdio compatibility.

What is not right yet:

- HTTP without a key is allowed.
- Static bearer tokens are not enough for production multi-user usage.
- The default host is `0.0.0.0`, which is risky for a command-executing security tool.
- No TLS guidance, reverse-proxy guidance, origin/CORS policy, audit trail, request rate limiting, or approval workflow.
- The remote/local scope filter is too coarse and too permissive.

Verdict: the transport choice is correct; the production security model around it is incomplete.

## Where ShikariMCP is better than HexStrike

- It directly addresses HexStrike's commonly cited local-only/stdio limitation by adding HTTP transport.
- Its scope-aware concept is a useful foundation for separating local machine tools from remote-safe tools.
- The codebase is small and easy to reason about compared with a more mature platform.

## Where ShikariMCP is worse than HexStrike and pentest-mcp

- HexStrike and pentest-mcp advertise fewer tools, but their public docs name real security tools. Shikari's inflated count includes many non-existent generated binaries.
- pentest-mcp appears more mature on transport/auth positioning: stdio, HTTP streaming, SSE, and OAuth 2.1.
- Shikari's agents are mostly mocked, while competitors position their agents around actual workflows.
- Shikari has no real policy engine, approvals, audit trails, or production deployment hardening.

## Where ShikariMCP differs from Penligent and Shannon

Penligent and Shannon are not simple "lots of CLI wrappers" projects. They focus on outcomes:

- verified exploit paths
- attack-chain simulation
- source-aware or context-aware analysis
- evidence and reporting
- governance and CI/CD usage

Shikari currently focuses on exposing tools. To compete with those products, the next step is not adding more wrappers; it is making fewer wrappers reliable, safe, structured, and reportable.

## Highest-priority fixes

1. Replace fake generated wrappers with a verified manifest.
   Keep generated files out of default registration unless each binary exists and has a tested command template.

2. Harden HTTP mode.
   Require auth by default, bind to localhost by default, add explicit unsafe flags, add audit logs, and add rate limits.

3. Implement dependency health.
   Honor `binary` and `requires_binaries`; expose installed/missing/degraded status.

4. Fix command execution model.
   Add stdin support, avoid shell syntax in strings, and convert wrappers to list-style commands.

5. Reclassify tool scopes.
   Default active and unknown tools to `LOCAL`; add approval-required capabilities.

6. Convert agents from mock to real.
   Start with `ReconAgent`, `PentestAgent`, and `BugBountyAgent`; remove no-op agents from production.

7. Add structured results and parsers.
   Start with Nmap, Nuclei, SQLMap, Nikto, FFUF/Gobuster, Hashcat/John.

8. Fix tests and add integration tests.
   Use `sys.executable`; test HTTP auth; test a mocked binary execution; test remote scope blocking; test duplicate-name detection.

## Bottom line

ShikariMCP has a good product instinct: "HexStrike-like security MCP, but usable over HTTP." That idea is valid. The current code is not yet a reliable implementation of that promise. The immediate path to strength is to reduce the claimed surface, verify real tools, harden HTTP, and make output structured and auditable. Once those are in place, Shikari can be a stronger practical MCP security toolkit than a local-only wrapper suite.
