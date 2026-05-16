"""Tests for structured tool output parsers."""

from shikari.parsers import (
    ffuf,
    httpx,
    katana,
    naabu,
    nmap,
    nuclei,
    sqlmap,
    subfinder,
    trivy,
    whois,
)


def test_nmap_xml_parser():
    raw = """<?xml version="1.0"?><nmaprun><host><address addr="127.0.0.1" addrtype="ipv4"/><ports><port protocol="tcp" portid="80"><state state="open"/><service name="http" product="nginx" version="1.25"/></port></ports></host></nmaprun>"""
    parsed = nmap.parse_xml(raw)
    assert parsed.assets[0].value == "127.0.0.1"
    assert parsed.services[0].port == 80
    assert parsed.services[0].name == "http"


def test_subfinder_jsonl_parser():
    parsed = subfinder.parse_jsonl('{"host":"api.example.com","source":"crtsh"}\n')
    assert parsed.assets[0].value == "api.example.com"


def test_httpx_jsonl_parser():
    parsed = httpx.parse_jsonl('{"url":"https://example.com","status_code":200,"title":"Example","tech":["nginx"]}\n')
    assert parsed.endpoints[0].url == "https://example.com"
    assert parsed.endpoints[0].technologies == ["nginx"]


def test_nuclei_jsonl_parser():
    raw = '{"template-id":"test","matched-at":"https://example.com","info":{"name":"Example vuln","severity":"high"}}\n'
    parsed = nuclei.parse_jsonl(raw)
    assert parsed.findings[0].title == "Example vuln"
    assert parsed.findings[0].severity == "high"


def test_naabu_jsonl_parser():
    parsed = naabu.parse_jsonl('{"host":"example.com","port":443}\n')
    assert parsed.services[0].port == 443


def test_katana_jsonl_parser():
    parsed = katana.parse_jsonl('{"url":"https://example.com/login"}\n')
    assert parsed.endpoints[0].url.endswith("/login")


def test_ffuf_json_parser():
    parsed = ffuf.parse_jsonl('{"results":[{"url":"https://example.com/admin","status":403}]}')
    assert parsed.endpoints[0].status_code == 403


def test_sqlmap_text_parser():
    parsed = sqlmap.parse_text("Parameter id is vulnerable. injectable")
    assert parsed.findings[0].severity == "high"


def test_trivy_json_parser():
    raw = '{"Results":[{"Target":"app","Vulnerabilities":[{"VulnerabilityID":"CVE-1","PkgName":"openssl","Severity":"CRITICAL"}]}]}'
    parsed = trivy.parse_json(raw)
    assert parsed.findings[0].severity == "critical"


def test_whois_parser():
    parsed = whois.parse_text("Domain Name: EXAMPLE.COM\n")
    assert parsed.assets[0].value == "example.com"
