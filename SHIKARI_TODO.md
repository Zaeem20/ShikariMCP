# ShikariMCP TODO

Date: 2026-05-16

This is the active implementation checklist for the local-first ShikariMCP goal: a standalone MCP server that lets AI clients orchestrate real security tools installed on the user's machine.

## Done

- [x] Harden HTTP startup so auth is required by default.
- [x] Default runtime host to `127.0.0.1`.
- [x] Add explicit `--allow-unauthenticated-http` development escape hatch.
- [x] Hide generated wrappers by default.
- [x] Add dependency metadata and missing-binary checks.
- [x] Add JSONL audit logging for tool execution.
- [x] Add output truncation and stdin support to the executor.
- [x] Add duplicate tool aliasing instead of silent overwrites.
- [x] Replace mocked workflow behavior in key agents with real command plans.
- [x] Add production readiness review and plan documents.
- [x] Fix README to show verified/default vs generated wrappers honestly.
- [x] Fix `pyproject.toml` stale `1000+ tools` claim.
- [x] Add `.gitignore` / `.dockerignore` hygiene.
- [x] Harden Docker Compose so it requires a real `SHIKARI_API_KEY`.
- [x] Add `core` manifest profile.
- [x] Add `shikari tools list`.
- [x] Add `shikari tools verify --profile core --json`.
- [x] Add MCP tools for manifest catalog and profile verification.
- [x] Add `scripts/install-tools.sh --profile core`.
- [x] Add `scripts/verify-tools.sh --profile core --json`.
- [x] Document currently supported integrations in README.

## P0 - Finish Local-First Foundation

- [x] Add `.env.docker.example` with safe Docker Compose defaults.
- [x] Update `.env.example` to include manifest/profile settings.
- [x] Add `SHIKARI_TOOL_PROFILE=core` config value.
- [x] Add `shikari tools explain <tool_id>` CLI.
- [x] Add MCP tool `shikari_explain_tool`.
- [x] Add a `tools.lock` file for pinned installer/Docker versions.
- [x] Make installer consume `tools.lock.json` for Go tool install refs.
- [x] Align Docker Go toolchain and core pins with `tools.lock.json` where pins are known.
- [x] Add installer dry-run test coverage.
- [x] Add Docker build smoke test to CI or local docs.

## P1 - Manifest-Driven Execution

- [x] Add `src/shikari/core/tool_runner.py`.
- [x] Build commands from manifest templates instead of each wrapper inventing its own command.
- [x] Add `shikari_run_verified_tool` MCP tool.
- [x] Add `shikari tools run <tool_id>` CLI for local debugging.
- [x] Add `shikari tools dry-run <tool_id>` CLI for local debugging.
- [x] Add dry-run mode that shows exact argv, timeout, stdin usage, and risk class.
- [x] Add structured run result model:
  - `run_id`
  - `tool`
  - `status`
  - `target`
  - `command`
  - `findings`
  - `assets`
  - `artifacts`
  - `errors`
  - `next_suggestions`
- [x] Store raw outputs as artifacts instead of dumping large blobs into LLM context.

## P2 - Parsers and Evidence

- [x] Add `src/shikari/parsers/`.
- [x] Add normalized models for:
  - `Asset`
  - `Service`
  - `Endpoint`
  - `Technology`
  - `Finding`
  - `Evidence`
  - `Artifact`
- [x] Implement parser: Nmap XML.
- [x] Implement parser: Subfinder JSONL.
- [x] Implement parser: httpx JSONL.
- [x] Implement parser: Nuclei JSONL.
- [x] Implement parser: Naabu JSONL.
- [x] Implement parser: Katana JSONL.
- [x] Implement parser: ffuf JSON/JSONL.
- [x] Implement parser: Nikto JSON.
- [x] Implement parser: SQLMap text/output directory.
- [x] Implement parser: Trivy JSON.
- [x] Add fixture tests for every parser.

## P3 - Agent Upgrade

- [x] Rewrite `ReconAgent` to use manifest runner and structured results.
- [x] Rewrite `PentestAgent` to use structured `nmap -> nuclei` evidence.
- [x] Rewrite `BugBountyAgent` to use structured `subfinder -> httpx -> nuclei`.
- [x] Add `WebAppAgent` or promote existing web domain agent into a production workflow.
- [x] Make agents return degraded status when tools are missing, not vague failures.
- [x] Make agents produce short human summaries plus machine-readable evidence.
- [x] Stop exposing generic/catalog-only agents as production agents unless they have domain-specific logic.

## P4 - Practical Local Safety Controls

- [x] Add simple local safety flags:
  - `--enable-active-tools`
  - `--enable-offensive-tools`
  - `--enable-credential-tools`
- [x] Add target allowlist for HTTP/local mode:
  - domains
  - CIDRs
  - filesystem roots
- [x] Block cloud metadata IPs by default.
- [x] Add `shikari policy explain` CLI.
- [x] Add MCP tool `shikari_policy_explain`.
- [x] Add workflow dry-run before active/offensive execution.

## P5 - Installers and Docker Profiles

- [x] Split installer into profiles:
  - `core`
  - `web`
  - `cloud`
  - `forensics`
  - `offensive`
  - `full`
- [x] Add `scripts/install-go-tools.sh`.
- [x] Add `scripts/install-wordlists.sh`.
- [x] Add optional SecLists install.
- [x] Add macOS Homebrew best-effort support.
- [x] Add `docker/Dockerfile.core`.
- [x] Keep the production Docker image scoped to the verified core profile.
- [x] Keep broader workstation profiles in the host installer instead of privileged images.
- [x] Add hardened root-level Docker Compose deployment.
- [x] Add Docker verification step: `shikari tools verify --profile core --json`.

## P6 - Tool Profile Expansion

- [x] Promote `masscan` into a manifest profile.
- [x] Promote `sslscan` / `sslyze`.
- [x] Promote `whatweb`.
- [x] Promote `wafw00f`.
- [x] Promote `dnsx`.
- [x] Promote `tlsx`.
- [x] Promote `mapcidr`.
- [x] Promote `uncover`.
- [x] Promote `testssl.sh`.
- [x] Promote `dalfox`.
- [x] Promote `arjun`.
- [x] Promote `semgrep`.
- [x] Promote `gitleaks`.
- [x] Promote `checkov` or `kics`.
- [x] Promote `yara`.
- [x] Promote `volatility3`.
- [x] Promote `radare2` or `rizin`.
- [x] Promote `john` and `hashcat` as offline-only tools.
- [x] Keep `hydra`, `medusa`, Metasploit, payload generation, and post-exploitation tools disabled unless explicit offensive profile is enabled.

## Modern Arsenal Candidates

Recent web/doc checks suggest these are good next additions for the local-first profiles:

- `dnsx`: ProjectDiscovery DNS toolkit; good for DNS enrichment and brute-force support.
- `tlsx`: ProjectDiscovery TLS scanner; good for certificate, TLS, and CT log intelligence.
- `mapcidr`: ProjectDiscovery CIDR utility; good for target normalization and CIDR expansion/filtering.
- `uncover`: ProjectDiscovery exposed-host discovery across search engines.
- `asnmap`: useful companion for ASN-to-CIDR/asset workflows.
- `notify`: optional reporting/notification integration, but should be disabled by default.

## P7 - Quality and Release

- [x] Add CI workflow.
- [x] Test on Python 3.11, 3.12, 3.13.
- [x] Add Ubuntu integration tests with fake binaries.
- [x] Add Docker build test.
- [x] Add bash script linting with `shellcheck`.
- [x] Add docs for supported profiles.
- [x] Add docs for MCP clients: Claude Desktop, Cursor, VS Code, Codex.
- [x] Add sample reports generated from structured evidence.
- [x] Add release checklist.

## Not P0

These are useful later, but not required for the local-first standalone MCP goal:

- [ ] Enterprise RBAC.
- [ ] OAuth/JWT/token introspection.
- [ ] Multi-user hosted deployment.
- [ ] Web dashboard.
- [ ] Full approval workflow with separate approver identity.

## P8 - Production Runtime Hardening

- [x] Kill complete subprocess trees on timeout and MCP cancellation.
- [x] Drain subprocess output concurrently and bound in-memory output.
- [x] Store complete stdout/stderr and parsed evidence as confined artifacts.
- [x] Add background submit, poll, list, cancel, and artifact-read MCP APIs.
- [x] Move dependency scans, DNS policy checks, and parsing off the event loop.
- [x] Add stateful Streamable HTTP event replay.
- [x] Add Host and Origin validation for DNS-rebinding protection.
- [x] Block local-scope manifest tools in remote HTTP.
- [x] Fix allowlist prefix bypasses and cloud metadata hostname handling.
- [x] Hide legacy direct wrappers from the production MCP surface.
- [x] Reduce the default schema surface to implemented workflows and control APIs.
- [x] Add bounded tool inputs and target counts.
- [x] Separate services and endpoints in structured run results.
- [x] Make agent workflow steps execute independent DAG branches concurrently.
- [x] Pin the production Python and core external-tool dependency ranges.
- [x] Make the core installer exclude offensive, credential, and forensic suites.
- [x] Replace the broad Docker image with a non-root verified core image.
- [x] Add hardened root Compose deployment.
- [x] Add cancellation, artifact, HTTP-header, background-run, and policy regression tests.
- [x] Update README and deployment documentation to match actual behavior.
- [ ] Verify the Docker build on a machine with Docker Engine or in CI.
- [ ] Run the CI matrix on Python 3.11, 3.12, and 3.13.
