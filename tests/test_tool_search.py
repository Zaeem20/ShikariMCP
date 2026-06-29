"""Tests for the tool search module."""

from shikari.core.tool_search import search_tools


def test_search_returns_results_for_known_tool():
    results = search_tools("nmap", profile="core")
    assert len(results) >= 1
    nmap = next(r for r in results if r["tool_id"] == "nmap_scan")
    assert nmap["category"] == "reconnaissance"
    assert nmap["source"] == "manifest"
    assert "active_network" in nmap["capabilities"]


def test_search_returns_empty_for_no_match():
    results = search_tools("zzz_nonexistent_tool_zzz", profile="core")
    assert results == []


def test_search_empty_query_returns_empty():
    results = search_tools("", profile="core")
    assert results == []


def test_search_matches_category():
    results = search_tools("reconnaissance", profile="core")
    assert len(results) >= 1
    assert all(r["category"] == "reconnaissance" for r in results)


def test_search_matches_capability():
    results = search_tools("passive_recon", profile="osint")
    assert len(results) >= 1
    assert any("passive_recon" in r["capabilities"] for r in results)


def test_search_respects_limit():
    results = search_tools("scan", profile="full", limit=3)
    assert len(results) <= 3


def test_search_case_insensitive():
    results_lower = search_tools("nmap", profile="core")
    results_upper = search_tools("NMAP", profile="core")
    results_mixed = search_tools("NmAp", profile="core")
    assert len(results_lower) == len(results_upper) == len(results_mixed)
