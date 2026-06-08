"""Tests for Streamable HTTP Host and Origin validation."""

from shikari.core.http_security import _matches


def test_exact_and_wildcard_port_matches():
    assert _matches("localhost:8080", ["localhost:*"])
    assert _matches("https://example.com", ["https://example.com"])


def test_host_prefix_confusion_is_rejected():
    assert not _matches("localhost.evil.test:8080", ["localhost:*"])
    assert not _matches("https://example.com.evil.test", ["https://example.com"])


def test_empty_policy_denies():
    assert not _matches("localhost:8080", [])
