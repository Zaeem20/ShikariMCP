# Tools & Profiles

## Tool Catalog Model

ShikariMCP maintains three tiers of tool exposure:

| Tier | Default | Description |
|------|---------|-------------|
| Verified wrappers | Exposed | Manually written wrappers with tested execution logic |
| Manifest-backed tools | Exposed | Declarative profiles with command templates and parsers |
| Generated wrappers | Hidden | Auto-generated compatibility wrappers; opt-in only |

Use `shikari_status` for exact runtime tool counts. Availability depends on transport mode, safety flags, and installed binaries.

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
| **Nikto** | `nikto_scan` | Web application | Web server misconfiguration checks | JSON | `apt: nikto` |
| **SQLMap** | `sqlmap_scan` | Web application | Conservative SQL injection testing | Text | `apt: sqlmap` |
| **Trivy** | `trivy_scan` | Container/code security | Filesystem, image, dependency scanning | JSON | Official installer |
| **Whois** | `whois_lookup` | Reconnaissance | Domain/IP registration context | Text | `apt: whois` |

The broader registry also includes manual wrappers for `masscan`, `hashcat`, `john`, `hydra`, `sslscan`, `sslyze`, `binwalk`, `exiftool`, `aircrack-ng`, `tshark`, `tcpdump`, and others.

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

## Tool Categories (Full Registry)

| # | Category | Registered | Description |
|---|----------|-----------:|-------------|
| 1 | Reconnaissance | 65 | Passive/active recon, subdomain enum, DNS, port scanning |
| 2 | Enumeration | 30 | Network, web, SMB, AD, SNMP, service enumeration |
| 3 | Vulnerability Scanning | 193 | Network, web, CMS, SSL/TLS scanners |
| 4 | Web Application | 259 | SQLi, XSS, fuzzing, API testing, auth bypass, CMS checks |
| 5 | Exploitation | 158 | Exploit frameworks and validation tools |
| 6 | Post-Exploitation | 155 | Privilege escalation, lateral movement, persistence, C2 |
| 7 | Password Attacks | 108 | Hashcat, John, brute force, wordlist tools |
| 8 | Network Attacks | 64 | Sniffing, MITM, spoofing, DoS catalog entries |
| 9 | OSINT | 63 | People search, domain intel, social media, breach detection |
| 10 | Mobile | 52 | Android, iOS, mobile analysis and forensics |
| 11 | Cloud Security | 5 | AWS, Azure, GCP, multi-cloud security |
| 12 | Forensics | 4 | Memory, disk, network forensics, steganography |
| 13 | Wireless | 3 | WiFi, Bluetooth, RF tools |
| 14 | Reverse Engineering | 3 | Disassemblers, debuggers, binary analysis |
| 15 | Evasion & Payloads | 4 | AV evasion, WAF bypass, payload generation |
| 16 | Database | 2 | SQL/NoSQL injection checks |

Generated compatibility wrappers are present in the repository but disabled by default. They should not be treated as production integrations until promoted into a manifest profile.
