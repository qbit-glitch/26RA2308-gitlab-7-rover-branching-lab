"""Graders for Tasks 5-8 (tidy up, hotfix from the release commit, detached HEAD, shift summary)."""
from __future__ import annotations

import re
from typing import Iterable, Optional

from .context import Ctx
from .facts import BASELINE_SUBJECT, FINAL_BRANCHES, IDEA_SUBJECT, RELEASE_SUBJECT, THROWAWAY_SUBJECT, Facts
from .framework import Task
from .textutil import (
    branch_names, decorations, get_answer_int, get_answer_sha, oneline_entries, parse_branch_list, parse_status,
    same_sha, sha_matches, strip_decoration,
)

HOTFIX, RECOVERY = "hotfix/sensor-timeout", "experiment/detached-recovery"
HOTFIX_SUBJECT = "fix(sensor): raise echo timeout to 50 ms"
TEMP_SUBJECT = "temp: experiment from old commit"
LIMITS_LINES = ("#define SENSOR_TIMEOUT_MS 50", "#define SENSOR_MAX_CM 400", "#define SENSOR_MIN_CM 2")


def _signed_by_author(facts: Facts, sha: str, content: str) -> bool:
    """The text a student typed carries the name of the person who made the commit."""
    author = facts.author_name(sha)
    return bool(author) and author in content


def _gap(found: Iterable[str], wanted: Iterable[str]) -> str:
    """Explain a branch-set mismatch: which branches are extra and which are missing."""
    found_set, wanted_set = set(found), set(wanted)
    extra, missing = sorted(found_set - wanted_set), sorted(wanted_set - found_set)
    return f"extra branches: {', '.join(extra) or 'none'}; missing branches: {', '.join(missing) or 'none'}"


# -- Task 5 -----------------------------------------------------------------
def grade_task5(ctx: Ctx) -> Task:
    """Task 5: rename, safe delete, forced delete."""
    t = Task(5, "Tidy up", 10, ctx.repo_mode)
    f = ctx.facts
    names51 = branch_names(ctx.step("5.1"))
    t.check(1, "5.1 the branch is now called experiment/yolov8-baseline (old name gone)",
            lambda: "experiment/yolov8-baseline" in names51 and "experiment/yolo-baseline" not in names51)
    t.check(2, "5.2 the branch reflog says: Branch: renamed refs/heads/experiment/yolo-baseline to "
               "refs/heads/experiment/yolov8-baseline",
            lambda: "Branch: renamed refs/heads/experiment/yolo-baseline to refs/heads/experiment/yolov8-baseline"
            in ctx.step("5.2"))
    m53 = re.search(r"Deleted branch experiment/yolov8-baseline \(was ([0-9a-f]{7,40})\)", ctx.step("5.3"))
    t.check(2, "5.3 'Deleted branch experiment/yolov8-baseline (was <sha of main>)'",
            lambda: m53 is not None and sha_matches(m53.group(1), f.origin_tip))
    t.check(2, "5.4 git refuses -d on feature/discarded-idea: 'not fully merged'",
            lambda: "not fully merged" in ctx.step("5.4"))
    m55 = re.search(r"Deleted branch feature/discarded-idea \(was ([0-9a-f]{7,40})\)", ctx.step("5.5"))
    t.check(1, "5.5 -D deletes feature/discarded-idea ('Deleted branch ... (was <sha>)')", lambda: m55 is not None)
    t.check(1, "5.6 only main, feature/obstacle-avoidance and feature/path-planning remain",
            lambda: set(branch_names(ctx.step("5.6"))) == {"main", "feature/obstacle-avoidance",
                                                            "feature/path-planning"})

    def deleted_commit_is_real() -> bool:
        sha = f.reflog_commit(IDEA_SUBJECT)
        return (m55 is not None and sha is not None and sha_matches(m55.group(1), sha)
                and not f.contained_in_any_branch(sha))

    t.check(1, "live repo: the SHA pasted in 5.5 is your 'wip: try lidar...' commit and no branch contains it now",
            deleted_commit_is_real, needs_repo=True)
    return t


# -- Task 6 -----------------------------------------------------------------
def _hotfix_limits(f: Facts) -> Optional[str]:
    """The expected sensor_limits.h if hotfix/sensor-timeout is exactly one commit on the release commit that
    changes only that file, and the file's lines are exactly the expected three (blank lines are ignored).

    Returns the CANONICAL text, not the student's bytes, so nothing the student wrote is ever compiled or run."""
    above = f.commits_above(f.release, HOTFIX)
    if len(above) != 1 or above[0]["subject"] != HOTFIX_SUBJECT or above[0]["files"] != ["src/sensor_limits.h"]:
        return None
    if f.parent(str(above[0]["sha"])) != f.release:
        return None
    content = f.file_at(HOTFIX, "src/sensor_limits.h") or ""
    if tuple(line.rstrip() for line in content.splitlines() if line.strip()) != LIMITS_LINES:
        return None
    return "\n".join(LIMITS_LINES) + "\n"


def _c_test_ok(f: Facts) -> bool:
    """The C unit test passes with the student's (verified) sensor_limits.h."""
    limits = _hotfix_limits(f)
    return limits is not None and f.c_test_passes_with_limits(limits)


def grade_task6(ctx: Ctx) -> Task:
    """Task 6: hotfix branch from the release commit."""
    t = Task(6, "Hotfix from the release commit", 15, ctx.repo_mode)
    f = ctx.facts
    t.check(1, "6.1 the log shows the 'release: v0.1 field build' commit",
            lambda: any(strip_decoration(e.subject) == RELEASE_SUBJECT for e in oneline_entries(ctx.step("6.1"))))
    t.check(2, "ANSWER-2 is the SHA of the release commit",
            lambda: sha_matches(get_answer_sha(ctx.text, 2), f.release))
    s62 = ctx.step("6.2")
    entries62 = oneline_entries(s62)
    t.check(1, "6.2 output says: Switched to a new branch 'hotfix/sensor-timeout'",
            lambda: "Switched to a new branch 'hotfix/sensor-timeout'" in s62)
    t.check(1, "6.2 the branch starts on the release commit",
            lambda: bool(entries62) and sha_matches(entries62[-1].sha, f.release))
    s63 = ctx.step("6.3")
    t.check(2, "6.3 the unit test fails on the far-object case",
            lambda: re.search(r"\bFAIL", s63) is not None and "far object" in s63)
    s64 = ctx.step("6.4")
    t.check(2, "6.4 the diff changes '#define SENSOR_TIMEOUT_MS 5' to '... 50'",
            lambda: re.search(r"(?m)^-#define SENSOR_TIMEOUT_MS 5\s*$", s64) is not None
            and re.search(r"(?m)^\+#define SENSOR_TIMEOUT_MS 50\s*$", s64) is not None)
    s65 = ctx.step("6.5")
    t.check(1, "6.5 the test now prints ALL TESTS PASSED and no FAIL",
            lambda: "ALL TESTS PASSED" in s65 and re.search(r"\bFAIL", s65) is None)
    s66 = ctx.step("6.6")
    t.check(1, "6.6 commit output: [hotfix/sensor-timeout sha] fix(sensor): raise echo timeout to 50 ms, "
               "1 deletion and 1 inserted line (2 if you pressed Enter after the 0)",
            lambda: re.search(r"\[hotfix/sensor-timeout [0-9a-f]{7,}\] " + re.escape(HOTFIX_SUBJECT), s66)
            is not None and re.search(r"\b[12] insertions?\(\+\), 1 deletion\(-\)", s66) is not None)
    t.check(1, "6.7 the graph shows hotfix/sensor-timeout and main",
            lambda: {HOTFIX, "main"} <= decorations(ctx.step("6.7")))
    t.check(2, "live repo: hotfix/sensor-timeout is exactly one commit on the release commit that changes only "
               "src/sensor_limits.h, and the file holds exactly the three expected lines with the timeout at 50",
            lambda: _hotfix_limits(f) is not None, needs_repo=True)
    t.check(1, "live repo: the C unit test passes with your src/sensor_limits.h",
            lambda: _c_test_ok(f), needs_repo=True)
    return t


# -- Task 7 -----------------------------------------------------------------
def _recovery_ok(f: Facts, answer4: str) -> bool:
    """The rescue branch is exactly one commit on the baseline commit, adding only results/notes.txt."""
    above = f.commits_above(f.baseline, RECOVERY)
    if (len(above) != 1 or above[0]["subject"] != TEMP_SUBJECT or above[0]["files"] != ["results/notes.txt"]
            or above[0]["added"] != ["results/notes.txt"]):
        return False
    content = f.file_at(RECOVERY, "results/notes.txt") or ""
    return _signed_by_author(f, str(above[0]["sha"]), content) and same_sha(answer4, str(above[0]["sha"]))


def _orphan_ok(f: Facts) -> bool:
    """The abandoned commit exists, sits on the baseline commit and no branch contains it."""
    sha = f.reflog_commit(THROWAWAY_SUBJECT)
    return sha is not None and f.parent(sha) == f.baseline and not f.contained_in_any_branch(sha)


def grade_task7(ctx: Ctx) -> Task:
    """Task 7: detached HEAD, rescue one commit, abandon one."""
    t = Task(7, "Detached HEAD", 15, ctx.repo_mode)
    f = ctx.facts
    t.check(1, "7.1 the log of results/experiments.txt shows the baseline run",
            lambda: any(strip_decoration(e.subject) == BASELINE_SUBJECT for e in oneline_entries(ctx.step("7.1"))))
    t.check(1, "ANSWER-3 is the SHA of the baseline run commit",
            lambda: sha_matches(get_answer_sha(ctx.text, 3), f.baseline))
    t.check(1, "7.2 git tells you that you are in 'detached HEAD' state", lambda: "detached HEAD" in ctx.step("7.2"))
    s73 = ctx.step("7.3")
    t.check(1, "7.3 the detector reproduces accuracy=0.750", lambda: "accuracy=0.750" in s73)
    t.check(1, "7.3 git status says 'HEAD detached at <sha>'",
            lambda: re.search(r"HEAD detached at [0-9a-f]{7,}", s73) is not None)
    m74 = re.search(r"\[detached HEAD ([0-9a-f]{7,40})\] " + re.escape(TEMP_SUBJECT), ctx.step("7.4"))
    t.check(1, "7.4 commit output: [detached HEAD sha] temp: experiment from old commit", lambda: m74 is not None)
    t.check(1, "ANSWER-4 is the SHA printed in 7.4",
            lambda: m74 is not None and same_sha(get_answer_sha(ctx.text, 4), m74.group(1)))
    s75 = ctx.step("7.5")
    entries75 = oneline_entries(s75)
    t.check(1, "7.5 output says: Switched to a new branch 'experiment/detached-recovery'",
            lambda: "Switched to a new branch 'experiment/detached-recovery'" in s75)
    t.check(1, "7.5 the log shows your temp commit on top of the baseline commit",
            lambda: len(entries75) >= 2 and TEMP_SUBJECT in entries75[0].subject
            and sha_matches(entries75[1].sha, f.baseline))
    t.check(1, "7.6 commit output: [detached HEAD sha] temp: throwaway idea",
            lambda: re.search(r"\[detached HEAD [0-9a-f]{7,}\] " + re.escape(THROWAWAY_SUBJECT), ctx.step("7.6"))
            is not None)
    s77 = ctx.step("7.7")
    t.check(2, "7.7 git warns: you are leaving 1 commit behind", lambda: "leaving 1 commit behind" in s77)
    t.check(1, "7.7 the reflog shows the checkout moves and your throwaway commit",
            lambda: "checkout: moving from" in s77
            and re.search(r"commit(?: \(amend\))?: " + re.escape(THROWAWAY_SUBJECT), s77) is not None)
    t.check(1, "live repo: experiment/detached-recovery is exactly one commit on the baseline commit, adds only "
               "results/notes.txt with your name, and ANSWER-4 is that commit",
            lambda: _recovery_ok(f, get_answer_sha(ctx.text, 4)), needs_repo=True)
    t.check(1, "live repo: your 'temp: throwaway idea' commit exists, sits on the baseline commit and no branch "
               "contains it",
            lambda: _orphan_ok(f), needs_repo=True)
    return t


# -- Task 8 -----------------------------------------------------------------
def grade_task8(ctx: Ctx) -> Task:
    """Task 8: shift summary."""
    t = Task(8, "Shift summary", 5, ctx.repo_mode)
    f = ctx.facts
    by = {r.name: r for r in parse_branch_list(ctx.step("8.1"))}
    t.check(2, "8.1 branch -vv lists exactly the five branches and main tracks [origin/main]",
            lambda: set(by) == FINAL_BRANCHES and by["main"].current and "[origin/main]" in by["main"].rest,
            why=lambda: _gap(by, FINAL_BRANCHES) if set(by) != FINAL_BRANCHES else "main is not on origin/main")
    s82 = ctx.step("8.2")
    st = parse_status(s82)
    t.check(1, "8.2 status: On branch main, up to date with origin/main, working tree clean",
            lambda: "On branch main" in s82 and st.up_to_date and st.clean)
    t.check(1, "ANSWER-5 is 5", lambda: get_answer_int(ctx.text, 5) == "5")
    t.check(1, "live repo: exactly those five local branches exist and main is still the published tip",
            lambda: set(f.local_branches()) == FINAL_BRANCHES and f.rev("main") == f.origin_tip, needs_repo=True,
            why=lambda: _gap(f.local_branches(), FINAL_BRANCHES) if set(f.local_branches()) != FINAL_BRANCHES
            else "main has moved away from the published tip (a commit was made on main)")
    return t
