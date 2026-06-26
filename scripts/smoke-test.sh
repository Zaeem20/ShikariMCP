#!/usr/bin/env bash
# ShikariMCP smoke test — runs without any external security binaries installed.
# Verifies: server startup, manifest loading, dry-run command building,
# policy engine, tool registry, and MCP tool surface.
#
# Usage: bash scripts/smoke-test.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"
if command -v uv >/dev/null 2>&1; then
  PYTHON_BIN="uv run python"
fi

PASS=0
FAIL=0

check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "  [PASS] $label"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] $label"
    FAIL=$((FAIL + 1))
  fi
}

echo "========================================"
echo " ShikariMCP Smoke Test (no binaries)"
echo "========================================"
echo

echo "[1] Python import and server module"
check "shikari.server imports" $PYTHON_BIN -c "from shikari.server import create_server; print('ok')"
check "shikari.config imports" $PYTHON_BIN -c "from shikari.config import ShikariConfig; print('ok')"
check "shikari.core.executor imports" $PYTHON_BIN -c "from shikari.core.executor import execute_command; print('ok')"
echo

echo "[2] Manifest profiles load"
for profile in core recon web cloud forensics offensive osint full; do
  check "profile '$profile' loads" $PYTHON_BIN -c "
from shikari.core.tool_manifest import load_tool_manifest
m = load_tool_manifest('$profile')
assert len(m.tools) > 0, 'no tools'
print(f'{len(m.tools)} tools')
"
done
echo

echo "[3] Tool registry discovery"
check "registry discovers tools" $PYTHON_BIN -c "
from shikari.core.registry import discover_tools
from shikari.tools._base import get_tool_registry
discover_tools()
r = get_tool_registry()
assert len(r) > 100, f'only {len(r)} tools'
print(f'{len(r)} wrappers')
"
echo

echo "[4] Dry-run command building (no execution)"
check "nmap dry-run builds command" $PYTHON_BIN -c "
from shikari.core.tool_runner import dry_run_verified_tool
r = dry_run_verified_tool('nmap_scan', {'target': 'example.com'}, 'core', 'safe')
cmd = r['command']['argv']
assert 'nmap' in cmd, f'nmap not in {cmd}'
assert 'example.com' in cmd, f'target not in {cmd}'
print(' '.join(cmd))
"
check "sherlock dry-run builds command" $PYTHON_BIN -c "
from shikari.core.tool_runner import dry_run_verified_tool
r = dry_run_verified_tool('sherlock_username', {'username': 'test'}, 'osint', 'safe')
cmd = r['command']['argv']
assert 'sherlock' in cmd, f'sherlock not in {cmd}'
print(' '.join(cmd))
"
check "shodan dry-run builds command" $PYTHON_BIN -c "
from shikari.core.tool_runner import dry_run_verified_tool
r = dry_run_verified_tool('shodan_host', {'ip': '8.8.8.8'}, 'osint', 'safe')
cmd = r['command']['argv']
assert 'shodan' in cmd, f'shodan not in {cmd}'
print(' '.join(cmd))
"
echo

echo "[5] Parsers import and handle empty input"
# Each parser has a specific function name — test with the correct one.
declare -A PARSER_FUNCS=(
  [sherlock]="parse_csv"
  [exiftool]="parse_json"
  [greynoise]="parse_json"
  [virustotal]="parse_json"
  [theharvester]="parse_text"
  [nmap]="parse_xml"
  [subfinder]="parse_jsonl"
  [httpx]="parse_jsonl"
  [nuclei]="parse_jsonl"
)
for parser in sherlock exiftool greynoise virustotal theharvester nmap subfinder httpx nuclei; do
  func="${PARSER_FUNCS[$parser]}"
  check "parser '$parser.$func' handles empty input" $PYTHON_BIN -c "
from shikari.parsers import parse_tool_output
result = parse_tool_output('shikari.parsers.$parser.$func', '')
assert result is not None, 'returned None'
print('ok')
"
done
echo

echo "[6] Policy engine"
check "policy explain works" $PYTHON_BIN -c "
from shikari.core.policy import explain_policy
r = explain_policy({})
assert isinstance(r, dict)
print('ok')
"
echo

echo "[7] Agent catalog plans"
check "all 47 catalog agents have real plans" $PYTHON_BIN -c "
from shikari.agents._catalog import build_default_plan, _PLANS
assert len(_PLANS) >= 45, f'only {len(_PLANS)} plans'
for name in _PLANS:
    plan = build_default_plan(name, 'example.com')
    assert len(plan) >= 1, f'{name} has empty plan'
    for step in plan:
        assert 'cmd' in step, f'{name} step missing cmd'
        assert isinstance(step['cmd'], list), f'{name} cmd not a list'
print(f'{len(_PLANS)} agents with real plans')
"
echo

echo "========================================"
echo " Results: $PASS passed, $FAIL failed"
echo "========================================"
exit $FAIL