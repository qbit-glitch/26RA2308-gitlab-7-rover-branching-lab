"""Tiny scoring framework: tasks made of weighted checks, each reported PASS/FAIL."""
from __future__ import annotations

from typing import Callable, List, NamedTuple, Optional, Union

Condition = Union[bool, Callable[[], bool]]


class CheckResult(NamedTuple):
    """Outcome of one check."""

    points: int
    description: str
    status: str  # "ok", "fail" or "skip"
    detail: str


class Task:
    """One assignment task: a title, a mark total and the checks that earn the marks."""

    def __init__(self, number: int, title: str, marks: int, repo_mode: bool) -> None:
        self.number = number
        self.title = title
        self.marks = marks
        self.repo_mode = repo_mode
        self.results: List[CheckResult] = []

    def check(self, points: int, description: str, condition: Condition,
              needs_repo: bool = False) -> None:
        """Record one check. 'condition' may be a bool or a function returning one."""
        if needs_repo and not self.repo_mode:
            self.results.append(CheckResult(points, description, "skip", "needs the live repo"))
            return
        detail = ""
        try:
            ok = bool(condition() if callable(condition) else condition)
        except Exception as exc:  # a malformed submission must never crash the grader
            ok, detail = False, f"could not evaluate ({type(exc).__name__}: {exc})"
        self.results.append(CheckResult(points, description, "ok" if ok else "fail", detail))

    def validate(self) -> None:
        """Developer safety net: the check weights must add up to the task's marks."""
        total = sum(r.points for r in self.results)
        if total != self.marks:
            raise AssertionError(f"Task {self.number}: check points add up to {total}, not {self.marks}")

    @property
    def earned(self) -> int:
        """Marks earned so far."""
        return sum(r.points for r in self.results if r.status == "ok")

    @property
    def possible(self) -> int:
        """Marks that could be earned in this mode (skipped checks excluded)."""
        return sum(r.points for r in self.results if r.status != "skip")

    @property
    def skipped(self) -> int:
        """Marks that were skipped because they need the live repo."""
        return sum(r.points for r in self.results if r.status == "skip")

    @property
    def passed(self) -> bool:
        """A task PASSES only when every non-skipped check passed."""
        return all(r.status != "fail" for r in self.results)


def format_report(tasks: List[Task], header: List[str], verbose: bool = True) -> str:
    """Render the full grading report as text."""
    lines: List[str] = list(header)
    lines.append("")
    for task in tasks:
        verdict = "PASS" if task.passed else "FAIL"
        lines.append(f"[{verdict}] Task {task.number}  {task.title:<44} {task.earned:>2}/{task.possible}")
        for result in task.results:
            if not verbose and result.status == "ok":
                continue
            tag = {"ok": "ok  ", "fail": "FAIL", "skip": "skip"}[result.status]
            extra = f"  -- {result.detail}" if result.detail else ""
            lines.append(f"         {tag} ({result.points}) {result.description}{extra}")
    earned = sum(t.earned for t in tasks)
    possible = sum(t.possible for t in tasks)
    skipped = sum(t.skipped for t in tasks)
    lines.append("")
    lines.append(f"TOTAL: {earned}/{possible}")
    if skipped:
        lines.append(f"({skipped} marks need the live repository and were skipped in --outputs-only mode)")
    lines.append(f"Tasks passed: {sum(1 for t in tasks if t.passed)}/{len(tasks)}")
    return "\n".join(lines)


def total_score(tasks: List[Task]) -> Optional[int]:
    """Total marks earned."""
    return sum(t.earned for t in tasks)
