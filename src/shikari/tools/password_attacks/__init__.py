# ShikariMCP — Password Attacks Module Exports

from .offline_cracking import hashcat_crack, john_crack
from .online_brute import hydra_brute, medusa_brute
from .wordlists import cewl_spider, crunch_generate

__all__ = [
    "hashcat_crack",
    "john_crack",
    "hydra_brute",
    "medusa_brute",
    "cewl_spider",
    "crunch_generate"
]
