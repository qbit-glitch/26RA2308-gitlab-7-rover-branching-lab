"""Shared grading context handed to every task grader."""
from __future__ import annotations

from typing import Dict, NamedTuple

from .facts import Facts


class Ctx(NamedTuple):
    """The parsed submission plus the facts needed to judge it."""

    steps: Dict[str, str]
    text: str
    facts: Facts
    repo_mode: bool

    def step(self, step_id: str) -> str:
        """Pasted text for a step id such as '2.3' ('' if missing)."""
        return self.steps.get(step_id, "")
