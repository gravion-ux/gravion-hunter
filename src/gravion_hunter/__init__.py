"""gravion-hunter — autonomous bug bounty agent framework."""

from .campaign import (
    GATE_QUESTIONS,
    ApprovalRequired,
    BrakeEngaged,
    Campaign,
    CampaignError,
    Row,
)
from .scope import Scope, ScopeError

__version__ = "0.1.0"

__all__ = [
    "GATE_QUESTIONS",
    "ApprovalRequired",
    "BrakeEngaged",
    "Campaign",
    "CampaignError",
    "Row",
    "Scope",
    "ScopeError",
    "__version__",
]
