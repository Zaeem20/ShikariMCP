# ShikariMCP - reusable agent plan catalog

from __future__ import annotations

import sys
from typing import Any


def build_default_plan(agent_name: str, target: str, **kwargs: Any) -> list[dict[str, Any]]:
    """
    Build a concrete, executable plan for every shipped agent.

    Each plan is a list of steps with a raw ``cmd`` list executed by the
    agent's ``execute()`` via :func:`shikari.core.executor.execute_command`.
    Plans use real, widely-available CLI security binaries. Offensive and
    credential-bearing commands are only reachable when the enclosing agent
    tool is exposed (the ``@shikari_tool`` capability gate on the agent
    category already enables ``--enable-offensive-tools`` /
    ``--enable-credential-tools`` opt-in).

    The goal is to make every shipped agent do real work without silently
    performing high-impact offensive actions. Riskier agents still lean on
    enumeration and evidence gathering rather than active exploitation.
    """
    target = str(target).strip()
    name = agent_name.lower()
    builder = _PLANS.get(name)
    if builder is None:
        # Fall back to a sensible recon plan instead of a no-op note so that
        # any future agent still does something useful by default.
        return _recon_plan(target)
    return builder(target)


# ---------------------------------------------------------------------------
# Step helpers
# ---------------------------------------------------------------------------

def _step(step_name: str, tool: str, cmd: list[str], timeout: int = 300) -> dict[str, Any]:
    return {"name": step_name, "tool": tool, "cmd": cmd, "timeout": timeout}


def _note_step(agent_name: str, target: str) -> dict[str, Any]:
    """Operator-guidance only step (reserved for genuinely no-op cases)."""
    message = (
        f"{agent_name} prepared an assessment plan for {target}. "
        "No high-impact action was executed because this agent requires an "
        "explicit approved runbook before running offensive or environment-changing tools."
    )
    return {
        "name": "operator_guidance",
        "tool": "policy_note",
        "cmd": [sys.executable, "-B", "-c", f"print({message!r})"],
    }


# ---------------------------------------------------------------------------
# Reusable plan fragments
# ---------------------------------------------------------------------------

def _recon_plan(target: str) -> list[dict[str, Any]]:
    return [
        _step("dns_lookup", "nslookup", ["nslookup", target]),
        _step("whois_lookup", "whois", ["whois", target]),
        _step("subdomain_enum", "subfinder", ["subfinder", "-d", target, "-silent"]),
    ]


def _web_plan(target: str) -> list[dict[str, Any]]:
    return [
        _step("web_fingerprint", "whatweb", ["whatweb", target]),
        _step("waf_detection", "wafw00f", ["wafw00f", target]),
        _step(
            "template_scan",
            "nuclei",
            [
                "nuclei", "-u", target, "-severity", "medium,high,critical",
                "-jsonl", "-silent", "-no-color",
            ],
        ),
    ]


def _network_plan(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step(
            "vulnerability_templates",
            "nuclei",
            [
                "nuclei", "-u", target, "-tags", "cve,exposure,misconfig",
                "-severity", "medium,high,critical", "-jsonl", "-silent", "-no-color",
            ],
        ),
    ]


def _file_triage_plan(target: str) -> list[dict[str, Any]]:
    """For forensics / malware / CTF / IOC agents where target is a file path."""
    return [
        _step("file_type", "file", ["file", target]),
        _step("embedded_content", "binwalk", ["binwalk", target]),
        _step("printable_strings", "strings", ["strings", "-n", "8", target]),
    ]


# ---------------------------------------------------------------------------
# Domain agents
# ---------------------------------------------------------------------------

def _webapp_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("web_fingerprint", "whatweb", ["whatweb", target]),
        _step("waf_detection", "wafw00f", ["wafw00f", target]),
        _step("content_fuzz", "ffuf", [
            "ffuf", "-u", f"{target}/FUZZ",
            "-w", "/usr/share/seclists/Discovery/Web-Content/common.txt",
            "-mc", "200,204,301,302,401,403", "-t", "20",
        ]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-severity", "medium,high,critical",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _network_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("host_discovery", "nmap", ["nmap", "-sn", target]),
        _step("service_scan", "nmap", ["nmap", "-sV", "-sC", "--top-ports", "1000", target]),
        _step("vuln_templates", "nuclei", [
            "nuclei", "-u", target, "-tags", "cve,exposure,misconfig",
            "-severity", "medium,high,critical", "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _cloud_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("config_scan", "trivy", ["trivy", "config", target]),
        _step("filesystem_scan", "trivy", [
            "trivy", "fs", "--scanners", "vuln,secret,misconfig", target,
        ]),
        _step("iac_scan", "checkov", ["checkov", "-d", target, "--framework", "terraform,kubernetes,dockerfile"]),
    ]


def _osint_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("whois_lookup", "whois", ["whois", target]),
        _step("dns_lookup", "nslookup", ["nslookup", target]),
        _step("subdomain_enum", "subfinder", ["subfinder", "-d", target, "-silent"]),
        _step("harvester", "theHarvester", [
            "theHarvester", "-d", target, "-b", "all", "-l", "500",
        ]),
        _step("shodan_host", "shodan", ["shodan", "host", target]),
        _step("greynoise_ip", "greynoise", ["greynoise", "ip", target, "-f", "json"]),
    ]


def _mobile_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("file_type", "file", ["file", target]),
        _step("apk_inspect", "apktool", ["apktool", "d", "-f", target]),
        _step("embedded_content", "binwalk", ["binwalk", target]),
        _step("printable_strings", "strings", ["strings", "-n", "8", target]),
    ]


def _ad_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("ldap_enum", "ldapsearch", [
            "ldapsearch", "-x", "-H", f"ldap://{target}",
            "-b", "", "sAMAccountName",
        ]),
        _step("smb_enum", "enum4linux-ng", ["enum4linux-ng", "-A", target]),
        _step("smb_shares", "nxc", ["nxc", "smb", target, "--shares", "--users"]),
    ]


def _malware_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("file_type", "file", ["file", target]),
        _step("printable_strings", "strings", ["strings", "-n", "8", target]),
        _step("embedded_content", "binwalk", ["binwalk", target]),
        _step("yara_scan", "yara", ["yara", "-r", "/usr/share/yara-rules", target]),
    ]


def _iot_scada_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("iot_port_scan", "nmap", [
            "nmap", "-sV", "-p",
            "23,502,1883,5683,47808,102,2404,4840",
            target,
        ]),
        _step("firmware_triage", "binwalk", ["binwalk", target]),
        _step("mqtt_probe", "mosquitto_sub", [
            "mosquitto_sub", "-h", target, "-t", "#", "-v", "-C", "50",
        ]),
    ]


def _database_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("db_service_scan", "nmap", [
            "nmap", "-sV", "-p",
            "1433,1521,3306,5432,6379,27017,9200,11211",
            "--script", "banner", target,
        ]),
        _step("db_vuln_templates", "nuclei", [
            "nuclei", "-u", target, "-tags", "db,misconfig",
            "-severity", "medium,high,critical", "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _wireless_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("wireless_host_discovery", "nmap", ["nmap", "-sn", target]),
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("wireless_iface_scan", "iwlist", ["iwlist", "scan"]),
    ]


# ---------------------------------------------------------------------------
# Intelligence agents
# ---------------------------------------------------------------------------

def _threatintel_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("whois_lookup", "whois", ["whois", target]),
        _step("shodan_host", "shodan", ["shodan", "host", target]),
        _step("greynoise_ip", "greynoise", ["greynoise", "ip", target, "-f", "json"]),
        _step("censys_host", "censys", ["censys", "view", "--id", target]),
        _step("vt_ip_lookup", "vt", ["vt", "ip", target, "--format", "json"]),
        _step("harvester", "theHarvester", ["theHarvester", "-d", target, "-b", "all"]),
    ]


def _cveintel_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("vuln_scripts", "nmap", ["nmap", "--script", "vuln", target]),
        _step("exploit_search", "searchsploit", ["searchsploit", target]),
    ]


def _zerodayresearch_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "-sC", target]),
        _step("vuln_scripts", "nmap", ["nmap", "--script", "vuln", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-tags", "cve,exposure,fuzz",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _report_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "-oX", "-", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-severity", "low,medium,high,critical",
            "-jsonl", "-silent", "-no-color",
        ]),
        _step("filesystem_scan", "trivy", ["trivy", "fs", "--scanners", "vuln,secret", target]),
    ]


def _attacksurface_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("subdomain_enum", "subfinder", ["subfinder", "-d", target, "-silent"]),
        _step("alive_check", "httpx", ["httpx", "-u", target, "-title", "-tech-detect"]),
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "1000", target]),
    ]


def _exploitgen_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("vuln_scripts", "nmap", ["nmap", "--script", "vuln", target]),
        _step("exploit_search", "searchsploit", ["searchsploit", target]),
    ]


def _iocextractor_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("file_type", "file", ["file", target]),
        _step("printable_strings", "strings", ["strings", "-n", "8", target]),
        _step("yara_scan", "yara", ["yara", "-r", "/usr/share/yara-rules", target]),
    ]


def _vulncorrelator_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "1000", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-tags", "cve,exposure,misconfig",
            "-severity", "medium,high,critical", "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _riskscoring_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-severity", "medium,high,critical",
            "-jsonl", "-silent", "-no-color",
        ]),
        _step("filesystem_scan", "trivy", ["trivy", "fs", "--scanners", "vuln,secret", target]),
    ]


def _threatmodeling_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "1000", target]),
        _step("web_fingerprint", "whatweb", ["whatweb", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-tags", "exposure,misconfig",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


# ---------------------------------------------------------------------------
# Offensive agents (gated by agent_offensive capability)
# ---------------------------------------------------------------------------

def _privesc_agent(target: str) -> list[dict[str, Any]]:
    # Local privilege-escalation enumeration. target is ignored for host-level
    # checks; these run against the local host.
    return [
        _step("system_info", "uname", ["uname", "-a"]),
        _step("identity", "id", ["id"]),
        _step("suid_find", "find", ["find", "/", "-perm", "-4000", "-type", "f", "-exec", "ls", "-la", "{}", "+"]),
        _step("sudo_privs", "sudo", ["sudo", "-l"]),
        _step("cron_jobs", "ls", ["ls", "-la", "/etc/cron*"]),
    ]


def _lateralmovement_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("lateral_port_scan", "nmap", ["nmap", "-p", "22,135,139,445,3389,5985", "-sV", target]),
        _step("smb_enum", "nxc", ["nxc", "smb", target, "--shares", "--users"]),
        _step("ssh_probe", "nmap", ["nmap", "-p", "22", "--script", "ssh-auth-methods", target]),
    ]


def _evasion_agent(target: str) -> list[dict[str, Any]]:
    # Enumeration of evasion/payload capabilities (no active bypass executed).
    return [
        _step("payload_list", "msfvenom", ["msfvenom", "--list", "payloads"]),
        _step("encoder_list", "msfvenom", ["msfvenom", "--list", "encoders"]),
    ]


def _payloadcraft_agent(target: str) -> list[dict[str, Any]]:
    # target is interpreted as LHOST:LPORT for payload generation.
    return [
        _step("list_payloads", "msfvenom", ["msfvenom", "--list", "payloads"]),
        _step("list_formats", "msfvenom", ["msfvenom", "--list", "formats"]),
    ]


def _credharvest_agent(target: str) -> list[dict[str, Any]]:
    # Credential-tool capability enumeration (no live cracking by default).
    return [
        _step("hash_formats", "john", ["john", "--list=formats"]),
        _step("example_hashes", "hashcat", ["hashcat", "--example-hashes"]),
    ]


# ---------------------------------------------------------------------------
# Defensive agents
# ---------------------------------------------------------------------------

def _hardening_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("exposed_services", "nmap", ["nmap", "-sV", "--top-ports", "1000", target]),
        _step("config_scan", "trivy", ["trivy", "config", target]),
        _step("filesystem_scan", "trivy", ["trivy", "fs", "--scanners", "misconfig,secret", target]),
    ]


def _forensics_agent(target: str) -> list[dict[str, Any]]:
    return _file_triage_plan(target) + [
        _step("file_hashes", "sha256sum", ["sha256sum", target]),
    ]


def _malwaretriage_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("file_type", "file", ["file", target]),
        _step("printable_strings", "strings", ["strings", "-n", "8", target]),
        _step("yara_scan", "yara", ["yara", "-r", "/usr/share/yara-rules", target]),
        _step("file_hash", "sha256sum", ["sha256sum", target]),
    ]


def _anomalydetect_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("listening_ports", "ss", ["ss", "-tulpn"]),
        _step("whois_lookup", "whois", ["whois", target]),
    ]


def _containment_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("host_discovery", "nmap", ["nmap", "-sn", target]),
        _step("listening_ports", "ss", ["ss", "-tulpn"]),
        _step("firewall_rules", "iptables", ["iptables", "-L", "-n", "-v"]),
    ]


# ---------------------------------------------------------------------------
# Infrastructure agents
# ---------------------------------------------------------------------------

def _decisionengine_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-tags", "cve,exposure,misconfig",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _paramoptimizer_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("version_intensity_scan", "nmap", ["nmap", "-sV", "--version-intensity", "5", target]),
        _step("tuned_template_scan", "nuclei", [
            "nuclei", "-u", target, "-c", "50", "-rl", "30",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _ratelimiter_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("rate_limited_scan", "nmap", ["nmap", "--max-rate", "10", "-sV", target]),
        _step("throttled_templates", "nuclei", [
            "nuclei", "-u", target, "-rl", "10", "-c", "10",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _failurerecovery_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("retry_service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", "--max-retries", "3", target]),
        _step("retry_template_scan", "nuclei", [
            "nuclei", "-u", target, "-retries", "3",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _performancemonitor_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("timed_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", "--max-parallelism", "10", target]),
        _step("concurrent_templates", "nuclei", [
            "nuclei", "-u", target, "-c", "100",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _resourcescheduler_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("queued_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("queued_templates", "nuclei", [
            "nuclei", "-u", target, "-c", "25",
            "-jsonl", "-silent", "-no-color",
        ]),
    ]


def _healthcheck_agent(target: str) -> list[dict[str, Any]]:
    # target is ignored; this checks installed tool binaries.
    return [
        _step("nmap_health", "which", ["which", "nmap"]),
        _step("nuclei_health", "which", ["which", "nuclei"]),
        _step("httpx_health", "which", ["which", "httpx"]),
        _step("subfinder_health", "which", ["which", "subfinder"]),
        _step("trivy_health", "which", ["which", "trivy"]),
    ]


def _configmanager_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("nmap_version", "nmap", ["nmap", "--version"]),
        _step("nuclei_version", "nuclei", ["nuclei", "-version"]),
        _step("trivy_version", "trivy", ["trivy", "--version"]),
    ]


# ---------------------------------------------------------------------------
# Workflow agents (experimental tier)
# ---------------------------------------------------------------------------

def _codereview_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("semgrep_scan", "semgrep", ["semgrep", "scan", "--config", "auto", "--json", target]),
        _step("bandit_scan", "bandit", ["bandit", "-r", target, "-f", "json"]),
        _step("filesystem_scan", "trivy", ["trivy", "fs", "--scanners", "vuln,secret", target]),
    ]


def _ctf_agent(target: str) -> list[dict[str, Any]]:
    return _file_triage_plan(target) + [
        _step("file_hash", "sha256sum", ["sha256sum", target]),
    ]


def _redteam_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "-sC", "--top-ports", "1000", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-tags", "cve,exposure,misconfig",
            "-severity", "medium,high,critical", "-jsonl", "-silent", "-no-color",
        ]),
        _step("exploit_search", "searchsploit", ["searchsploit", target]),
    ]


def _blueteam_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("exposed_services", "nmap", ["nmap", "-sV", "--top-ports", "1000", target]),
        _step("listening_ports", "ss", ["ss", "-tulpn"]),
        _step("config_scan", "trivy", ["trivy", "config", target]),
    ]


def _purpleteam_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-severity", "medium,high,critical",
            "-jsonl", "-silent", "-no-color",
        ]),
        _step("listening_ports", "ss", ["ss", "-tulpn"]),
    ]


def _threathunt_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
        _step("listening_ports", "ss", ["ss", "-tulpn"]),
        _step("logins", "last", ["last", "-n", "50"]),
    ]


def _vulnmanagement_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("service_scan", "nmap", ["nmap", "-sV", "--top-ports", "1000", target]),
        _step("template_scan", "nuclei", [
            "nuclei", "-u", target, "-severity", "low,medium,high,critical",
            "-jsonl", "-silent", "-no-color",
        ]),
        _step("filesystem_scan", "trivy", ["trivy", "fs", "--scanners", "vuln", target]),
    ]


def _ir_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("host_discovery", "nmap", ["nmap", "-sn", target]),
        _step("listening_ports", "ss", ["ss", "-tulpn"]),
        _step("recent_logins", "last", ["last", "-n", "100"]),
    ]


def _compliance_agent(target: str) -> list[dict[str, Any]]:
    return [
        _step("config_scan", "trivy", ["trivy", "config", target]),
        _step("filesystem_scan", "trivy", ["trivy", "fs", "--scanners", "vuln,misconfig", target]),
        _step("exposed_services", "nmap", ["nmap", "-sV", "--top-ports", "100", target]),
    ]


# ---------------------------------------------------------------------------
# Plan registry
# ---------------------------------------------------------------------------

_PLANS: dict[str, Any] = {
    # Domain
    "webappagent": _webapp_agent,
    "networkagent": _network_agent,
    "cloudagent": _cloud_agent,
    "osintagent": _osint_agent,
    "mobileagent": _mobile_agent,
    "adagent": _ad_agent,
    "malwareagent": _malware_agent,
    "iotscadaagent": _iot_scada_agent,
    "databaseagent": _database_agent,
    "wirelessagent": _wireless_agent,
    # Intelligence
    "threatintelagent": _threatintel_agent,
    "cveintelagent": _cveintel_agent,
    "zerodayresearchagent": _zerodayresearch_agent,
    "reportagent": _report_agent,
    "attacksurfaceagent": _attacksurface_agent,
    "exploitgenagent": _exploitgen_agent,
    "iocextractoragent": _iocextractor_agent,
    "vulncorrelatoragent": _vulncorrelator_agent,
    "riskscoringagent": _riskscoring_agent,
    "threatmodelingagent": _threatmodeling_agent,
    # Offensive
    "privescagent": _privesc_agent,
    "lateralmovementagent": _lateralmovement_agent,
    "evasionagent": _evasion_agent,
    "payloadcraftagent": _payloadcraft_agent,
    "credharvestagent": _credharvest_agent,
    # Defensive
    "hardeningagent": _hardening_agent,
    "forensicsagent": _forensics_agent,
    "malwaretriageagent": _malwaretriage_agent,
    "anomalydetectagent": _anomalydetect_agent,
    "containmentagent": _containment_agent,
    # Infrastructure
    "decisionengineagent": _decisionengine_agent,
    "paramoptimizeragent": _paramoptimizer_agent,
    "ratelimiteragent": _ratelimiter_agent,
    "failurerecoveryagent": _failurerecovery_agent,
    "performancemonitoragent": _performancemonitor_agent,
    "resourcescheduleragent": _resourcescheduler_agent,
    "healthcheckagent": _healthcheck_agent,
    "configmanageragent": _configmanager_agent,
    # Workflow (experimental tier)
    "codereviewagent": _codereview_agent,
    "ctfagent": _ctf_agent,
    "redteamagent": _redteam_agent,
    "blueteamagent": _blueteam_agent,
    "purpleteamagent": _purpleteam_agent,
    "threathuntagent": _threathunt_agent,
    "vulnmanagementagent": _vulnmanagement_agent,
    "iragent": _ir_agent,
    "complianceagent": _compliance_agent,
}