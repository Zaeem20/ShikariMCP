"""Live integration test for ShikariMCP HTTP transport."""

import json

import httpx
import pytest

BASE = "http://127.0.0.1:9090/mcp"
HEADERS = {
    "Authorization": "Bearer test-secret-key-12345",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

INIT_PAYLOAD = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0"},
    },
}


def parse_sse(response):
    """Extract JSON from SSE or plain JSON response."""
    for line in response.text.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                return json.loads(line[6:])
            except json.JSONDecodeError:
                continue
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


@pytest.fixture(scope="module")
def session():
    """Initialize an MCP session and return session headers."""
    try:
        r = httpx.post(BASE, headers=HEADERS, json=INIT_PAYLOAD, timeout=10)
    except Exception as exc:  # pragma: no cover - server may not be running
        pytest.skip(f"ShikariMCP HTTP server not reachable at {BASE}: {exc}")
    session_id = r.headers.get("mcp-session-id", "")
    if not session_id:  # pragma: no cover
        pytest.skip("No mcp-session-id returned from initialize")
    return {**HEADERS, "mcp-session-id": session_id}


def test_initialize():
    r = httpx.post(BASE, headers=HEADERS, json=INIT_PAYLOAD, timeout=10)
    assert r.status_code == 200
    assert "mcp-session-id" in r.headers
    data = parse_sse(r)
    assert data is not None
    assert "result" in data
    assert "serverInfo" in data["result"]


def test_list_tools(session):
    payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    r = httpx.post(BASE, headers=session, json=payload, timeout=10)
    assert r.status_code == 200
    data = parse_sse(r)
    tools = data.get("result", {}).get("tools", []) if data else []
    tool_names = [t["name"] for t in tools]
    assert "shikari_status" in tool_names
    assert "shikari_run_tool" in tool_names
    assert "shikari_submit_tool" in tool_names
    assert "shikari_read_artifact" in tool_names
    assert "shikari_policy_explain" in tool_names
    assert len(tools) >= 317


def test_shikari_status(session):
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "shikari_status", "arguments": {}},
    }
    r = httpx.post(BASE, headers=session, json=payload, timeout=10)
    assert r.status_code == 200
    data = parse_sse(r)
    content = data["result"].get("content", [{}])
    text = content[0].get("text", "") if content else ""
    status_data = json.loads(text) if text.startswith("{") else {}
    assert "version" in status_data
    assert "transport" in status_data
    assert "tool_profile" in status_data


def test_shikari_policy_explain(session):
    payload = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "shikari_policy_explain", "arguments": {}},
    }
    r = httpx.post(BASE, headers=session, json=payload, timeout=10)
    assert r.status_code == 200
    data = parse_sse(r)
    content = data["result"].get("content", [{}])
    text = content[0].get("text", "") if content else ""
    policy_data = json.loads(text) if text.startswith("{") else {}
    assert "blocked_metadata_ips" in policy_data
    assert "target_allowlist" in policy_data


def test_input_validation_bad_tool_id(session):
    payload = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "shikari_run_tool",
            "arguments": {
                "tool_id": "nmap; rm -rf /",
                "inputs": {"target": "test"},
            },
        },
    }
    r = httpx.post(BASE, headers=session, json=payload, timeout=10)
    assert r.status_code == 200
    data = parse_sse(r)
    error_text = json.dumps(data)
    assert "Invalid tool_id" in error_text or "error" in error_text.lower()


def test_bad_profile_validation(session):
    payload = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "shikari_list_tools",
            "arguments": {"profile": "nonexistent_xyz"},
        },
    }
    r = httpx.post(BASE, headers=session, json=payload, timeout=10)
    assert r.status_code == 200
    data = parse_sse(r)
    error_text = json.dumps(data)
    assert "Unknown profile" in error_text or "error" in error_text.lower()


def test_rate_limiting_configured(session):
    payload = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {"name": "shikari_policy_explain", "arguments": {}},
    }
    r = httpx.post(BASE, headers=session, json=payload, timeout=10)
    assert r.status_code == 200
    data = parse_sse(r)
    content = data["result"].get("content", [{}])
    text = content[0].get("text", "") if content else ""
    policy_data = json.loads(text) if text.startswith("{") else {}
    assert policy_data.get("rate_limit_rps", 0) > 0
    assert policy_data.get("rate_limit_burst", 0) > 0

    for _ in range(5):
        r = httpx.post(BASE, headers=session, json=INIT_PAYLOAD, timeout=5)
        assert r.status_code == 200


def test_authentication_rejection():
    no_auth_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    r = httpx.post(BASE, headers=no_auth_headers, json=INIT_PAYLOAD, timeout=5)
    assert r.status_code in (401, 403)
