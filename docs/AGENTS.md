# Agents

ShikariMCP exposes four implemented workflow agents by default. The repository also retains a larger experimental agent catalog, but those entries are hidden unless experimental compatibility mode is enabled.

## Workflow Agents (13)

| Agent | Audience | Description |
|-------|----------|-------------|
| **ReconAgent** | Red team, bug bounty | Full recon pipeline — passive → subdomains → DNS → ports → services |
| **PentestAgent** | Red team, pentest | Complete pentest lifecycle — recon → vuln scan → exploit → report |
| **BugBountyAgent** | Bug bounty | Subdomain → fuzzing → param mining → injection |
| **WebAppWorkflowAgent** | Red team, bug bounty | Fingerprint → probe → crawl → templates → parameters |
| **CTFAgent** | CTF players | Identifies challenge type → selects tools → solves |
| **RedTeamAgent** | Red team | Full kill chain — access → privesc → lateral → persistence → exfil |
| **BlueTeamAgent** | Blue team | Defensive assessment — logs → detection gaps → hardening checks |
| **PurpleTeamAgent** | Purple team | Combined red+blue — attacks and validates detection capabilities |
| **IncidentResponseAgent** | Blue team, SOC | IR workflow — triage → containment → eradication → recovery |
| **ThreatHuntAgent** | Blue team, SOC | Proactive hunting — IOC search → behavioral analysis → YARA |
| **ComplianceAgent** | GRC, compliance | CIS, PCI-DSS, HIPAA, SOC2, ISO27001 auditing |
| **VulnManagementAgent** | Blue team, GRC | Vuln lifecycle — scan → prioritize → track → verify fix |
| **CodeReviewAgent** | DevSecOps | Source code security — SAST → secrets → dependencies → patterns |

## Intelligence Agents (10)

| Agent | Description |
|-------|-------------|
| **CVEIntelAgent** | CVE lookup, exploit availability, severity scoring |
| **ExploitGenAgent** | Analyzes vulnerabilities → generates PoC exploits → tests |
| **VulnCorrelatorAgent** | Attack chain discovery — maps chained vulnerabilities |
| **ThreatIntelAgent** | OSINT, breach databases, APT TTPs, MITRE ATT&CK |
| **AttackSurfaceAgent** | Maps all external assets — subdomains, APIs, cloud |
| **ReportAgent** | Aggregates findings → executive and technical reports |
| **IOCExtractorAgent** | Extracts IOCs from scan outputs → structured feeds |
| **RiskScoringAgent** | Context-aware risk scoring with business impact |
| **ZeroDayResearchAgent** | Fuzzing, crash analysis, PoC development |
| **ThreatModelingAgent** | STRIDE/DREAD threat modeling |

## Infrastructure Agents (8)

| Agent | Description |
|-------|-------------|
| **DecisionEngine** | Selects optimal tool combination for a given objective |
| **ParamOptimizer** | Tunes parameters based on context |
| **RateLimiter** | Detects WAFs → adjusts speed and rotates |
| **FailureRecovery** | Diagnoses failures → retries with adjusted parameters |
| **PerformanceMonitor** | Monitors resources → throttles if needed |
| **ResourceScheduler** | Queue prioritization and concurrent execution |
| **HealthCheckAgent** | Checks tool installations and dependencies |
| **ConfigManager** | Scan profiles and environment presets |

## Domain-Specific Agents (10)

| Agent | Description |
|-------|-------------|
| **WebAppAgent** | Full web app testing — spider → inject → auth bypass |
| **NetworkAgent** | Network security — discovery → scan → exploit → traffic analysis |
| **CloudAgent** | Multi-cloud — IAM, storage, serverless, compliance |
| **MobileAgent** | Android and iOS — reversing, hooking, certificate pinning |
| **OSINTAgent** | Full OSINT — people → email → social → breach → dossier |
| **ActiveDirectoryAgent** | AD attacks — Kerberoast, delegation, BloodHound |
| **MalwareAgent** | Static and dynamic analysis, IOC extraction, YARA |
| **IoTSCADAAgent** | Firmware, MQTT/CoAP/Modbus, PLC enumeration |
| **WirelessAgent** | WiFi, Bluetooth, and RF analysis |
| **DatabaseAgent** | SQL/NoSQL injection, privilege escalation |

## Offensive Agents (5)

These agents require `--enable-offensive-tools` to execute.

| Agent | Description |
|-------|-------------|
| **PrivEscAgent** | Linux SUID/cron/kernel and Windows tokens/services/UAC |
| **LateralMovementAgent** | Pass-the-hash, PSExec, WMI, SSH pivoting, SOCKS |
| **EvasionAgent** | AV/AMSI/ETW bypass, obfuscation, process injection |
| **PayloadCraftAgent** | Shellcode, staged/stageless, multi-platform, C2 |
| **CredHarvestAgent** | Mimikatz, LSASS, SAM, Kerberos tickets, NTDS |

## Defensive Agents (5)

| Agent | Description |
|-------|-------------|
| **HardeningAgent** | OS benchmarks, service minimization, firewall rules |
| **ForensicsAgent** | Memory, disk, network, and log forensics |
| **MalwareTriageAgent** | Classification, hash lookup, YARA, sandbox, IOCs |
| **AnomalyDetectAgent** | Log analysis, network anomalies, behavioral alerts |
| **ContainmentAgent** | Network isolation, lockout, firewall, DNS sinkhole |
