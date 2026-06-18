# ShikariMCP Production Readiness Report

Date: 2026-06-09

## Verdict

ShikariMCP now has a production-grade baseline for a standalone, single-user MCP server running on a practitioner's machine. The default surface is compact, policy-controlled, non-blocking, and backed by real manifest commands.

Release is ready for Docker/CI verification. Docker Engine is not installed on the audit machine, and Ruff was not available in the offline package cache, so those two checks must complete in GitHub Actions or another build host before tagging a release.

## Closed Findings

- Long scans no longer need to hold an MCP request open.
- MCP cancellation and timeouts terminate the complete subprocess tree.
- stdout and stderr are drained concurrently, bounded in memory, and retained as artifacts.
- dependency scans, DNS checks, parsing, and artifact reads do not block the event loop.
- Streamable HTTP uses authenticated stateful sessions, SSE event replay, and Host/Origin checks.
- local-scope and active tools cannot silently cross remote HTTP policy boundaries.
- allowlist prefix confusion and cloud metadata endpoint bypasses are blocked.
- caller-controlled output paths are replaced with confined artifact paths.
- auxiliary files such as wordlists are not mistaken for network targets.
- the production MCP surface is 16 focused tools rather than the 1,219-entry compatibility catalog.
- four implemented workflows execute independent dependency branches concurrently.
- core tool versions are pinned in manifests, the lock file, installer, and Docker image.
- the core installer no longer installs credential, offensive, packet-capture, or forensic suites.
- the production container is non-root and the Compose deployment is read-only and capability-restricted.

## Validation

- Python tests: 117 passed.
- Python bytecode compilation: passed.
- Manifest and lock JSON parsing: passed.
- CI and Compose YAML parsing: passed.
- Bash syntax checks with Git Bash: passed.
- Authenticated HTTP initialize: `200`, session ID present, SSE response.
- Live HTTP tool listing: 16 tools in about 0.03 seconds.
- Live HTTP status call: about 0.03 seconds.
- Live background submission: about 0.03 seconds.
- Cancellation regression test confirms descendants do not survive.

## Remaining Operational Limits

- Background run state and SSE replay events are process-local. Artifacts persist, but queued/running state does not survive a server restart.
- The API-key model is intended for one trusted user or one trusted client boundary, not a multi-tenant hosted service.
- Legacy and generated wrappers remain compatibility code and are not production-supported integrations.
- External tools can change behavior independently. Pins should move only after parser and installer tests pass.
- Raw-socket tools in Docker require `NET_RAW`; Compose grants only that capability.

## Research Basis

- [MCP Streamable HTTP transport](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [FastMCP HTTP deployment](https://gofastmcp.com/deployment/http)
- [FastMCP background tasks](https://gofastmcp.com/servers/tasks)
- [ProjectDiscovery httpx](https://github.com/projectdiscovery/httpx)
- [ProjectDiscovery Nuclei releases](https://github.com/projectdiscovery/nuclei/releases)
- [ProjectDiscovery Subfinder releases](https://github.com/projectdiscovery/subfinder/releases)
- [Trivy installation](https://trivy.dev/docs/latest/getting-started/installation/)
- [Nikto](https://github.com/sullo/nikto)
- [SQLMap](https://github.com/sqlmapproject/sqlmap)
