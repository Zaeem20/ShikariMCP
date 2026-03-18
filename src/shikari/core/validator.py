# ShikariMCP — Input Validation & Sanitization

import re
import ipaddress
import logging

logger = logging.getLogger("shikari.validator")

# Dangerous characters for command injection
DANGEROUS_CHARS = set(";|&$`\\!><\n\r")

# Common valid patterns
DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)
PORT_RANGE_REGEX = re.compile(r"^(\d{1,5}(-\d{1,5})?,?)+$|^-$")


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def sanitize_input(value: str, context: str = "input") -> str:
    """
    Sanitize a string input by removing dangerous characters.
    Raises ValidationError if the input is suspicious.
    """
    if not value or not value.strip():
        raise ValidationError(f"Empty {context} provided")

    # Check for command injection attempts
    found = DANGEROUS_CHARS.intersection(value)
    if found:
        chars = ", ".join(repr(c) for c in found)
        raise ValidationError(
            f"Dangerous characters detected in {context}: {chars}. "
            f"Possible command injection attempt."
        )

    return value.strip()


def validate_target(target: str) -> str:
    """
    Validate a target (IP, domain, or CIDR).
    Returns the cleaned target string.
    """
    target = sanitize_input(target, "target")

    # Check if it's an IP address or CIDR
    try:
        ipaddress.ip_address(target)
        return target
    except ValueError:
        pass

    try:
        ipaddress.ip_network(target, strict=False)
        return target
    except ValueError:
        pass

    # Check if it's a valid domain
    if DOMAIN_REGEX.match(target):
        return target

    raise ValidationError(
        f"Invalid target: '{target}'. Must be an IP address, CIDR range, or domain name."
    )


def validate_port(port: str) -> str:
    """Validate a port specification (single port, range, or comma-separated)."""
    port = sanitize_input(port, "port")

    if port == "-":  # All ports
        return port

    if not PORT_RANGE_REGEX.match(port):
        raise ValidationError(
            f"Invalid port specification: '{port}'. "
            f"Use a single port (80), range (80-443), or comma-separated (80,443,8080)."
        )

    # Validate individual port numbers
    for part in port.replace("-", ",").split(","):
        if part and int(part) > 65535:
            raise ValidationError(f"Port {part} is out of range (0-65535)")

    return port


def validate_url(url: str) -> str:
    """Validate a URL."""
    url = sanitize_input(url, "URL")

    if not url.startswith(("http://", "https://")):
        raise ValidationError(
            f"Invalid URL: '{url}'. Must start with http:// or https://"
        )

    return url


def validate_path(path: str) -> str:
    """Validate a file path (basic sanitization)."""
    path = sanitize_input(path, "path")

    # Prevent path traversal
    if ".." in path:
        raise ValidationError(
            f"Path traversal detected in '{path}'. '..' is not allowed."
        )

    return path
