#!/usr/bin/env python3
"""Automatic grader for the Rover Branching Git lab.

Usage (from inside your clone):
    python3 tests/grade.py                   # grade submission/outputs.txt against your repo
    python3 tests/grade.py --outputs-only    # grade only the pasted text (no live-repo checks)
    python3 tests/grade.py --submission path/to/outputs.txt --repo path/to/clone

Exit status is 0 when every task passes, 1 otherwise, 2 for set-up problems.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import List, Optional

sys.dont_write_bytecode = True  # grading must never leave __pycache__ folders in your clone
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from autograde.context import Ctx  # noqa: E402
from autograde.facts import Facts, GitError  # noqa: E402
from autograde.framework import Task, format_report  # noqa: E402
from autograde.integrity import integrity_warnings  # noqa: E402
from autograde.tasks_a import grade_task1, grade_task2, grade_task3, grade_task4  # noqa: E402
from autograde.tasks_b import grade_task5, grade_task6, grade_task7, grade_task8  # noqa: E402
from autograde.textutil import header_field, normalise, parse_steps, safe_text  # noqa: E402

REPO_ROOT = os.path.dirname(HERE)
DEFAULT_SUBMISSION = os.path.join(REPO_ROOT, "submission", "outputs.txt")
GRADERS = [grade_task1, grade_task2, grade_task3, grade_task4,
           grade_task5, grade_task6, grade_task7, grade_task8]


def write_report(target: str, content: str) -> None:
    """Write the report file, but never through a link: a student's folder could point results.txt elsewhere."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(target, flags, 0o644)
    except OSError:
        print(f"note: {os.path.basename(target)} was not written (it is a link or cannot be written)")
        return
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description="Grade the Rover Branching Git lab.")
    parser.add_argument("--submission", default=DEFAULT_SUBMISSION, help="pasted-outputs file")
    parser.add_argument("--repo", default=REPO_ROOT, help="the student's clone (default: this repo)")
    parser.add_argument("--outputs-only", action="store_true",
                        help="skip checks that need the live repo (for grading a submitted file)")
    parser.add_argument("--no-report", action="store_true", help="do not write submission/results.txt")
    parser.add_argument("--brief", action="store_true", help="only list checks that failed")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Run all task graders and print the report."""
    args = parse_args(argv)
    if not os.path.isfile(args.submission):
        print(f"Submission file not found: {args.submission}\n"
              "Create it with:  cp submission/outputs.template.txt submission/outputs.txt")
        return 2
    try:
        facts = Facts(args.repo)
    except GitError as exc:
        print(f"Cannot grade: {exc}")
        return 2
    with open(args.submission, encoding="utf-8", errors="replace") as handle:
        text = normalise(handle.read())
    ctx = Ctx(steps=parse_steps(text), text=text, facts=facts, repo_mode=not args.outputs_only)

    tasks: List[Task] = []
    for grader in GRADERS:
        task = grader(ctx)
        task.validate()
        tasks.append(task)

    who = safe_text(header_field(text, "Name")) or "(name not filled in)"
    reg = safe_text(header_field(text, "Reg No")) or "(reg no not filled in)"
    header = [
        "Rover Branching Lab - automatic grader",
        f"Student : {who}   {reg}",
        f"Mode    : {'outputs-only (no live-repo checks)' if args.outputs_only else 'full (pasted outputs + live repo)'}",
        f"Graded  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    report = format_report(tasks, header, verbose=not args.brief)
    warnings = integrity_warnings(ctx)
    for warning in warnings:
        report += f"\nINTEGRITY WARNING: {safe_text(warning)}"
    print(report)
    if not args.no_report and not args.outputs_only:
        write_report(os.path.join(os.path.dirname(os.path.abspath(args.submission)), "results.txt"), report + "\n")
    return 0 if all(task.passed for task in tasks) else 1


if __name__ == "__main__":
    sys.exit(main())
