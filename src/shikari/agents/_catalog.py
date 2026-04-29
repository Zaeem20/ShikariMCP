# ShikariMCP - reusable agent plan catalog

from __future__ import annotations

import sys
from typing import Any


def build_default_plan(agent_name: str, target: str, **kwargs: Any) -> list[dict[str, Any]]:
    """
    Build a conservative, executable plan for scaffolded agents.

    The goal is to make every shipped agent do real work without silently
    performing high-impact offensive actions. Riskier agents produce operator
    guidance unless a future explicit approval workflow expands their plan.
    """
    target = str(target).strip()
    name = agent_name.lower()

    if any(token in name for token in ("web", "bugbounty")):
        return [
            {"name": "web_fingerprint", "tool": "whatweb", "cmd": ["whatweb", target]},
            {"name": "waf_detection", "tool": "wafw00f", "cmd": ["wafw00f", target]},
            {
                "name": "template_scan",
                "tool": "nuclei",
                "cmd": [
                    "nuclei",
                    "-u",
                    target,
                    "-severity",
                    "medium,high,critical",
                    "-jsonl",
                    "-silent",
                    "-no-color",
                ],
            },
        ]

    if any(token in name for token in ("recon", "attack surface", "attacksurface", "osint")):
        return [
            {"name": "dns_lookup", "tool": "nslookup", "cmd": ["nslookup", target]},
            {"name": "whois_lookup", "tool": "whois", "cmd": ["whois", target]},
            {"name": "subdomain_enum", "tool": "subfinder", "cmd": ["subfinder", "-d", target, "-silent"]},
        ]

    if any(token in name for token in ("network", "pentest", "vuln", "purple")):
        return [
            {"name": "service_scan", "tool": "nmap", "cmd": ["nmap", "-sV", "--top-ports", "100", target]},
            {
                "name": "vulnerability_templates",
                "tool": "nuclei",
                "cmd": [
                    "nuclei",
                    "-u",
                    target,
                    "-tags",
                    "cve,exposure,misconfig",
                    "-severity",
                    "medium,high,critical",
                    "-jsonl",
                    "-silent",
                    "-no-color",
                ],
            },
        ]

    if any(token in name for token in ("code", "cloud", "container", "compliance", "hardening")):
        return [
            {"name": "config_scan", "tool": "trivy", "cmd": ["trivy", "config", target]},
            {"name": "filesystem_scan", "tool": "trivy", "cmd": ["trivy", "fs", "--scanners", "vuln,secret,misconfig", target]},
        ]

    if any(token in name for token in ("forensics", "malware", "reverse", "mobile", "ctf")):
        return [
            {"name": "file_type", "tool": "file", "cmd": ["file", target]},
            {"name": "embedded_content", "tool": "binwalk", "cmd": ["binwalk", target]},
        ]

    if any(
        token in name
        for token in (
            "red",
            "exploit",
            "evasion",
            "payload",
            "cred",
            "lateral",
            "privesc",
            "containment",
            "ir",
            "threat",
            "risk",
            "report",
            "ioc",
            "ratelimiter",
            "scheduler",
            "decision",
            "config",
            "failure",
            "performance",
            "optimizer",
            "health",
        )
    ):
        return [_note_step(agent_name, target)]

    return [_note_step(agent_name, target)]


def _note_step(agent_name: str, target: str) -> dict[str, Any]:
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
