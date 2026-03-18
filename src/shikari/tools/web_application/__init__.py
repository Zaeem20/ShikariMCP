# ShikariMCP — Web Application Tools Module

from . import injection
from . import fuzzing
from . import api_testing
from . import proxy_tools
from . import auth_testing
from . import cms_exploitation

__all__ = [
    "injection",
    "fuzzing",
    "api_testing",
    "proxy_tools",
    "auth_testing",
    "cms_exploitation"
]
