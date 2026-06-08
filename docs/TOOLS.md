# Tools & Profiles

## Tool Catalog Model

ShikariMCP maintains three tiers of tool integration:

| Tier | Default | Description |
|------|---------|-------------|
| Manifest-backed tools | Default | Reviewed command templates, policy, artifacts, and parsers |
| Workflow agents | Default | Four implemented evidence-driven workflows |
| Legacy/generated wrappers | Hidden | Compatibility catalog; opt-in and not the production path |

The default MCP schema contains 16 focused tools. External binaries are invoked through `shikari_run_verified_tool` or `shikari_submit_verified_tool`; they are not each exposed as a separate MCP schema.

## Supported Profiles

| Profile | Purpose | Integrations |
|---------|---------|-------------|
| `core` | Default local-first recon, probing, web scan, container/code scan | Nmap, Subfinder, httpx, Nuclei, Naabu, Katana, ffuf, Gobuster, Nikto, SQLMap, Trivy, Whois |
| `recon` | Asset discovery and target normalization | Masscan, dnsx, mapcidr, uncover |
| `web` | Web application testing extras | WhatWeb, wafw00f, testssl.sh, Dalfox, Arjun, SSLScan, tlsx |
| `cloud` | Code, secrets, IaC, and container security | Semgrep, Gitleaks, Checkov |
| `forensics` | Local analysis and reverse engineering | YARA, Volatility3, Radare2 |
| `offensive` | Explicit opt-in offline/credential testing | John, Hashcat, Hydra |
| `full` | Combined workstation arsenal | Aggregates all profiles |

## Core Integrations

These tools are listed in `src/shikari/manifests/tools/core.json` and are the primary verified set.

| Tool | Shikari ID | Category | Purpose | Output | Install |
|------|------------|----------|---------|--------|---------|
| **Nmap** | `nmap_scan` | Reconnaissance | Service/version discovery, host and CIDR scanning | XML | `apt: nmap` |
| **Subfinder** | `subfinder_enum` | Reconnaissance | Passive subdomain enumeration | JSONL | Go install |
| **httpx** | `httpx_probe` | Reconnaissance | HTTP probing, status, title, tech detection | JSONL | Go install |
| **Nuclei** | `nuclei_scan` | Vulnerability scanning | Template-based vulnerability checks | JSONL | Go install |
| **Naabu** | `naabu_scan` | Reconnaissance | Fast port discovery | JSONL | Go install + `libpcap` |
| **Katana** | `katana_crawl` | Web application | Crawling and endpoint discovery | JSONL | Go install |
| **ffuf** | `ffuf_fuzz` | Web application | Directory/content fuzzing | JSON/JSONL | Go install |
| **Gobuster** | `gobuster_dir` | Web application | Directory brute forcing | Text | Go install |
| **Nikto** | `nikto_scan` | Web application | Web server misconfiguration checks | JSON | Official GitHub release |
| **SQLMap** | `sqlmap_scan` | Web application | Conservative SQL injection testing | Text | Official GitHub release |
| **Trivy** | `trivy_scan` | Container/code security | Filesystem, image, dependency scanning | JSON | Official installer |
| **Whois** | `whois_lookup` | Reconnaissance | Domain/IP registration context | Text | `apt: whois` |

The compatibility registry also contains direct wrappers, but it is hidden unless `SHIKARI_ENABLE_LEGACY_TOOLS=true`.

## Install and Verify

### Debian/Ubuntu/Kali

```bash
# Install the core profile
./scripts/install-tools.sh --profile core

# Verify installed binaries
./scripts/verify-tools.sh --profile core --json

# Or use the Python CLI directly
shikari tools verify --profile core --json
```

### Preview Commands

```bash
# Explain a tool's purpose and command structure
shikari tools explain nmap_scan

# Preview the exact command without executing
shikari tools dry-run nmap_scan --input target=scanme.nmap.org
```

The installer is profile-based and intentionally conservative. It installs only the tools declared in the selected profile manifest, not every experimental wrapper in the repository.

Generated compatibility wrappers are present for migration and experimentation. They should not be treated as supported integrations until promoted into a reviewed manifest profile.
