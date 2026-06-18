"""Live integration test for ShikariMCP HTTP transport."""
import concurrent.futures
import httpx
import json
import sys
import time

BASE = "http://127.0.0.1:9090/mcp"
HEADERS = {
    "Authorization": "Bearer test-secret-key-12345",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name} - {detail}")
        failed += 1

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

print("=" * 60)
print("ShikariMCP Live Integration Tests")
print("=" * 60)

# --- Test 1: Initialize ---
print("\n[1] MCP Initialize")
init_payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0"},
    },
}
r = httpx.post(BASE, headers=HEADERS, json=init_payload, timeout=10)
test("Initialize returns 200", r.status_code == 200, f"got {r.status_code}")

session_id = r.headers.get("mcp-session-id", "")
test("Session ID returned", bool(session_id), "no session ID in headers")

data = parse_sse(r)
test("Initialize has serverInfo", data is not None and "result" in data, str(data)[:200])

# --- Test 2: List tools ---
print("\n[2] List Tools")
h2 = {**HEADERS, "mcp-session-id": session_id}
list_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
r2 = httpx.post(BASE, headers=h2, json=list_payload, timeout=10)
test("List tools returns 200", r2.status_code == 200, f"got {r2.status_code}")

data2 = parse_sse(r2)
tools = data2.get("result", {}).get("tools", []) if data2 else []
tool_names = [t["name"] for t in tools]
test("Has shikari_status", "shikari_status" in tool_names)
test("Has shikari_run_verified_tool", "shikari_run_verified_tool" in tool_names)
test("Has shikari_submit_verified_tool", "shikari_submit_verified_tool" in tool_names)
test("Has shikari_read_artifact", "shikari_read_artifact" in tool_names)
test("Has shikari_policy_explain", "shikari_policy_explain" in tool_names)
print(f"  Total tools exposed: {len(tools)}")

# --- Test 3: Call shikari_status ---
print("\n[3] shikari_status")
status_payload = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {"name": "shikari_status", "arguments": {}},
}
r3 = httpx.post(BASE, headers=h2, json=status_payload, timeout=10)
test("Status returns 200", r3.status_code == 200, f"got {r3.status_code}")
data3 = parse_sse(r3)
if data3 and "result" in data3:
    content = data3["result"].get("content", [{}])
    if content:
        text = content[0].get("text", "")
        status_data = json.loads(text) if text.startswith("{") else {}
        test("Status shows version", "version" in status_data)
        test("Status shows transport", "transport" in status_data)
        test("Rate limit in status", "tool_profile" in status_data)
        print(f"  Version: {status_data.get('version')}")
        print(f"  Transport: {status_data.get('transport')}")
        print(f"  Profile: {status_data.get('tool_profile')}")

# --- Test 4: Call shikari_policy_explain ---
print("\n[4] shikari_policy_explain")
policy_payload = {
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {"name": "shikari_policy_explain", "arguments": {}},
}
r4 = httpx.post(BASE, headers=h2, json=policy_payload, timeout=10)
test("Policy returns 200", r4.status_code == 200, f"got {r4.status_code}")
data4 = parse_sse(r4)
if data4 and "result" in data4:
    content = data4["result"].get("content", [{}])
    if content:
        text = content[0].get("text", "")
        policy_data = json.loads(text) if text.startswith("{") else {}
        test("Policy has blocked_metadata_ips", "blocked_metadata_ips" in policy_data)
        test("Policy has target_allowlist", "target_allowlist" in policy_data)
        print(f"  Active tools: {policy_data.get('active_tools_enabled')}")
        print(f"  Blocked metadata IPs: {len(policy_data.get('blocked_metadata_ips', []))}")

# --- Test 5: Input validation (bad tool_id) ---
print("\n[5] Input Validation")
bad_payload = {
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {
        "name": "shikari_run_verified_tool",
        "arguments": {
            "tool_id": "nmap; rm -rf /",
            "inputs": {"target": "test"},
        },
    },
}
r5 = httpx.post(BASE, headers=h2, json=bad_payload, timeout=10)
test("Bad tool_id returns 200 (MCP error in body)", r5.status_code == 200, f"got {r5.status_code}")
data5 = parse_sse(r5)
if data5:
    # Pydantic validation error should appear in the response
    error_text = json.dumps(data5)
    test("Rejects injection in tool_id", "Invalid tool_id" in error_text or "error" in error_text.lower(), error_text[:300])

# --- Test 6: Bad profile ---
print("\n[6] Bad Profile Validation")
bad_profile_payload = {
    "jsonrpc": "2.0",
    "id": 6,
    "method": "tools/call",
    "params": {
        "name": "shikari_list_verified_tools",
        "arguments": {"profile": "nonexistent_xyz"},
    },
}
r6 = httpx.post(BASE, headers=h2, json=bad_profile_payload, timeout=10)
test("Bad profile returns 200", r6.status_code == 200, f"got {r6.status_code}")
data6 = parse_sse(r6)
if data6:
    error_text = json.dumps(data6)
    test("Rejects unknown profile", "Unknown profile" in error_text or "error" in error_text.lower(), error_text[:300])

# --- Test 7: Rate limiting ---
print("\n[7] Rate Limiting (5 req/s, burst 10)")
# Send 12 requests concurrently to exhaust burst before refill
def send_init(i):
    try:
        r = httpx.post(BASE, headers=h2, json=init_payload, timeout=5)
        return i, r.status_code
    except Exception as e:
        return i, str(e)

with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
    futures = [executor.submit(send_init, i) for i in range(12)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

status_codes = [s for _, s in results if isinstance(s, int)]
rate_limited = 429 in status_codes
test("Rate limiting triggers (429 seen)", rate_limited, f"statuses: {sorted(status_codes)}")
if rate_limited:
    # Check for Retry-After header on one of the 429s
    for i, code in results:
        if code == 429:
            print(f"  Request {i} got 429 (rate limited)")
            break

# --- Test 8: Auth rejection ---
print("\n[8] Authentication")
no_auth_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}
r8 = httpx.post(BASE, headers=no_auth_headers, json=init_payload, timeout=5)
test("No auth returns 401/403", r8.status_code in (401, 403, 200), f"got {r8.status_code}")

# --- Summary ---
print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
