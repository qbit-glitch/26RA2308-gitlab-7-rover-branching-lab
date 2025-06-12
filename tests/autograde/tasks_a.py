"""Graders for Tasks 1-4 (look around, open work streams, parallel work, the big picture)."""
from __future__ import annotations

import re
from typing import List

from .context import Ctx
from .facts import IDEA_SUBJECT, Facts
from .framework import Task
from .textutil import (
    BranchRow, branch_names, decorations, first_match, get_answer_int, parse_branch_list, parse_config_list,
    sha_matches,
)

PLACEHOLDER_NAMES = {"", "your full name", "your name"}
PLACEHOLDER_EMAILS = {"", "your.email@example.com"}
FIVE_BRANCHES = {"main", "feature/obstacle-avoidance", "feature/path-planning",
                 "experiment/yolo-baseline", "feature/discarded-idea"}
OBSTACLE, PLANNING = "feature/obstacle-avoidance", "feature/path-planning"
AVOID_SUBJECT = "feat(nav): add obstacle avoidance stub"
PLANNER_SUBJECT = "feat(nav): add path planner stub"
ORIGINAL_FIRST_LINE = "/* controller.c - motion commands for the Kestrel-1 rover */"


def _signed_by_author(facts: Facts, sha: str, content: str) -> bool:
    """The text a student typed carries the name of the person who made the commit."""
    author = facts.author_name(sha)
    return bool(author) and author in content


# -- Task 1 -----------------------------------------------------------------
def grade_task1(ctx: Ctx) -> Task:
    """Task 1: set up, then look around (branch -v/-a, HEAD, the 41-byte ref file)."""
    t = Task(1, "Arrive and look around", 10, ctx.repo_mode)
    f = ctx.facts
    cfg = parse_config_list(ctx.step("1.1"))
    name, email = cfg.get("user.name", ""), cfg.get("user.email", "")
    t.check(2, "1.1 user.name and user.email are your own details (not the placeholders)",
            lambda: name.lower() not in PLACEHOLDER_NAMES and "@" in email and email.lower() not in PLACEHOLDER_EMAILS)
    t.check(1, "1.1 alias.tree is set to 'log --oneline --graph --decorate --all'",
            lambda: cfg.get("alias.tree") == "log --oneline --graph --decorate --all")
    rows = parse_branch_list(ctx.step("1.2"))
    t.check(1, "1.2 only the branch main exists, it is checked out, and it is on the published tip",
            lambda: len(rows) == 1 and rows[0].current and rows[0].name == "main"
            and sha_matches(rows[0].sha, f.origin_tip))
    names13 = branch_names(ctx.step("1.3"))
    t.check(1, "1.3 lists remotes/origin/HEAD and remotes/origin/main",
            lambda: "remotes/origin/HEAD" in names13 and "remotes/origin/main" in names13)
    s14 = ctx.step("1.4")
    t.check(1, "1.4 HEAD file says 'ref: refs/heads/main'", lambda: "ref: refs/heads/main" in s14)
    t.check(1, "1.4 refs/heads/main holds the 40-digit SHA of the published tip",
            lambda: first_match(r"\b[0-9a-f]{40}\b", s14) == f.origin_tip)
    t.check(1, "1.4 wc -c reports 41 bytes (40 hex digits + newline)",
            lambda: re.search(r"(?m)^\s*41\s*$", s14) is not None)
    t.check(2, "live repo: the pasted identity is the one configured in this clone and is not a teammate's",
            lambda: bool(name) and name == f.config_value("user.name") and email == f.config_value("user.email")
            and name.lower() not in f.published_names() and email.lower() not in f.published_emails(),
            needs_repo=True)
    return t


# -- Task 2 -----------------------------------------------------------------
def _same_tip(rows: List[BranchRow]) -> bool:
    """Three new branches sit on main's commit; feature/discarded-idea is one commit ahead."""
    by = {r.name: r for r in rows}
    tip = by["main"].sha
    same = ("feature/obstacle-avoidance", "feature/path-planning", "experiment/yolo-baseline")
    return all(by[n].sha == tip for n in same) and by["feature/discarded-idea"].sha != tip


def _idea_commit_ok(f: Facts) -> bool:
    """The wip commit (found in the reflog, its branch is deleted later) sits on the published tip."""
    sha = f.reflog_commit(IDEA_SUBJECT)
    if not sha or f.parent(sha) != f.origin_tip:
        return False
    above = f.commits_above(f.origin_tip, sha)
    content = f.file_at(sha, "IDEAS.txt") or ""
    return len(above) == 1 and above[0]["files"] == ["IDEAS.txt"] and _signed_by_author(f, sha, content)


def _streams_ok(f: Facts) -> bool:
    """Both surviving feature branches are built on the published tip, and the wip commit is sound."""
    branches = f.local_branches()
    for branch in (OBSTACLE, PLANNING):
        if branch not in branches or not f.is_ancestor(f.origin_tip, branches[branch]):
            return False
    return _idea_commit_ok(f)


def _switch_order_ok(f: Facts) -> bool:
    """HEAD reflog shows moves to the four new branches in order, then back to main."""
    moves = [e["msg"] for e in reversed(f.head_reflog()) if e["msg"].startswith("checkout: moving from")]
    targets = [m.rsplit(" to ", 1)[1] for m in moves]
    order = ["feature/obstacle-avoidance", "feature/path-planning", "experiment/yolo-baseline",
             "feature/discarded-idea", "main"]
    position = 0
    for target in targets:
        if position < len(order) and target == order[position]:
            position += 1
    return position == len(order)


def grade_task2(ctx: Ctx) -> Task:
    """Task 2: create branches in four ways."""
    t = Task(2, "Open work streams", 15, ctx.repo_mode)
    f = ctx.facts
    for sid, msg in (("2.1", "Switched to branch 'feature/obstacle-avoidance'"),
                     ("2.2", "Switched to a new branch 'feature/path-planning'"),
                     ("2.3", "Switched to a new branch 'experiment/yolo-baseline'"),
                     ("2.4", "Switched to a new branch 'feature/discarded-idea'")):
        t.check(1, f"{sid} output says: {msg}", lambda sid=sid, msg=msg: msg in ctx.step(sid))
    s25 = ctx.step("2.5")
    t.check(1, "2.5 commit output shows the subject 'wip: try lidar for obstacle detection' on feature/discarded-idea",
            lambda: re.search(r"\[feature/discarded-idea [0-9a-f]{7,}\] " + re.escape(IDEA_SUBJECT), s25) is not None)
    t.check(1, "2.5 commit output reports '1 file changed' with 1 inserted line (2 if you pressed Enter at the end)",
            lambda: re.search(r"\b1 file changed, (?:1 insertion|2 insertions)\(\+\)", s25) is not None)
    rows = parse_branch_list(ctx.step("2.6"))
    t.check(2, "2.6 branch -v lists exactly the five branches with * on main",
            lambda: {r.name for r in rows} == FIVE_BRANCHES and {r.name: r for r in rows}["main"].current)
    t.check(1, "2.6 three branches sit on the commit of main; feature/discarded-idea is one commit ahead",
            lambda: _same_tip(rows))
    t.check(3, "live repo: the two feature branches still descend from the published tip, and the wip commit "
               "sits on that tip, adds only IDEAS.txt and carries your name",
            lambda: _streams_ok(f), needs_repo=True)
    t.check(1, "live repo: the SHA pasted in 2.5 is that commit (paste the output of your last commit command)",
            lambda: sha_matches((re.findall(r"\[feature/discarded-idea ([0-9a-f]{7,40})\]", s25) or [""])[-1],
                                f.reflog_commit(IDEA_SUBJECT) or ""), needs_repo=True)
    t.check(2, "live repo: HEAD reflog shows you moved to the four new branches in order and back to main",
            lambda: _switch_order_ok(f), needs_repo=True)
    return t


# -- Task 3 -----------------------------------------------------------------
def _stream_ok(f: Facts, branch: str, subject: str, path: str, needles: List[str], new_file: bool) -> bool:
    """Branch is exactly one commit on the published tip, touching only 'path', signed with the student's name."""
    above = f.commits_above(f.origin_tip, branch)
    if len(above) != 1 or above[0]["subject"] != subject or above[0]["files"] != [path]:
        return False
    if new_file and above[0]["added"] != [path]:
        return False
    content = f.file_at(branch, path) or ""
    return _signed_by_author(f, str(above[0]["sha"]), content) and all(n in content for n in needles)


def grade_task3(ctx: Ctx) -> Task:
    """Task 3: independent commits on two branches; switching changes the files."""
    t = Task(3, "Two features in parallel", 20, ctx.repo_mode)
    f = ctx.facts
    s31, s32 = ctx.step("3.1"), ctx.step("3.2")
    t.check(2, "3.1 commit output: [feature/obstacle-avoidance sha] feat(nav): add obstacle avoidance stub",
            lambda: re.search(r"\[feature/obstacle-avoidance [0-9a-f]{7,}\] " + re.escape(AVOID_SUBJECT), s31)
            is not None)
    t.check(1, "3.1 reports '1 file changed'", lambda: re.search(r"\b1 file changed", s31) is not None)
    t.check(2, "3.2 commit output: [feature/path-planning sha] feat(nav): add path planner stub",
            lambda: re.search(r"\[feature/path-planning [0-9a-f]{7,}\] " + re.escape(PLANNER_SUBJECT), s32)
            is not None)
    t.check(1, "3.2 shows 'create mode 100644 tools/planner.py'",
            lambda: "create mode 100644 tools/planner.py" in s32)
    s33, s34, s35 = ctx.step("3.3"), ctx.step("3.4"), ctx.step("3.5")
    t.check(2, "3.3 on feature/obstacle-avoidance: tools has no planner.py and controller.c starts with 'void avoid'",
            lambda: "detector.py" in s33 and "planner.py" not in s33 and "void avoid(void)" in s33)
    t.check(2, "3.4 on feature/path-planning: tools has planner.py and controller.c is the original",
            lambda: "planner.py" in s34 and "void avoid" not in s34 and ORIGINAL_FIRST_LINE in s34)
    t.check(2, "3.5 on main: tools has no planner.py and controller.c is the original",
            lambda: "detector.py" in s35 and "planner.py" not in s35 and "void avoid" not in s35
            and ORIGINAL_FIRST_LINE in s35)
    s36 = ctx.step("3.6")
    t.check(2, "3.6 diff --stat between the two branches lists both files ('2 files changed')",
            lambda: "src/controller.c" in s36 and "tools/planner.py" in s36 and "2 files changed" in s36)
    t.check(3, "live repo: feature/obstacle-avoidance is exactly one commit on the published tip, changes only "
               "src/controller.c, contains 'void avoid(void)' and your name",
            lambda: _stream_ok(f, OBSTACLE, AVOID_SUBJECT, "src/controller.c", ["void avoid(void)"], False),
            needs_repo=True)
    t.check(3, "live repo: feature/path-planning is exactly one commit on the published tip, adds only "
               "tools/planner.py, contains 'def plan' and your name",
            lambda: _stream_ok(f, PLANNING, PLANNER_SUBJECT, "tools/planner.py", ["def plan"], True),
            needs_repo=True)
    return t


# -- Task 4 -----------------------------------------------------------------
def grade_task4(ctx: Ctx) -> Task:
    """Task 4: graph, merged and not merged."""
    t = Task(4, "The big picture", 10, ctx.repo_mode)
    s41 = ctx.step("4.1")
    need = FIVE_BRANCHES | {"origin/main"}
    t.check(3, "4.1 graph shows all five branches and origin/main, and the lines fork",
            lambda: need <= decorations(s41) and re.search(r"\|/|\|\\|/ /", s41) is not None)
    t.check(2, "4.2 branch -a lists the five local branches and remotes/origin/main",
            lambda: (FIVE_BRANCHES | {"remotes/origin/main"}) <= set(branch_names(ctx.step("4.2"))))
    t.check(2, "4.3 --merged lists exactly main and experiment/yolo-baseline",
            lambda: set(branch_names(ctx.step("4.3"))) == {"main", "experiment/yolo-baseline"})
    t.check(2, "4.4 --no-merged lists exactly feature/discarded-idea, feature/obstacle-avoidance, "
               "feature/path-planning",
            lambda: set(branch_names(ctx.step("4.4"))) == {"feature/discarded-idea", OBSTACLE, PLANNING})
    t.check(1, "ANSWER-1 is 3 (branches that hold work main does not have)",
            lambda: get_answer_int(ctx.text, 1) == "3")
    return t
