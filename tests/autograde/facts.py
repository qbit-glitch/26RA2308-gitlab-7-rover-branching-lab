"""Ground truth about the repository: the published history and the student's live repo."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

STAFF_SUBJECT = "chore: add lab assignment and grader"
RELEASE_SUBJECT = "release: v0.1 field build"
BASELINE_SUBJECT = "experiment: baseline detector run at threshold 0.40"
BUG_SUBJECT = "perf(sensor): shorten echo timeout to 5 ms"
IDEA_SUBJECT = "wip: try lidar for obstacle detection"
THROWAWAY_SUBJECT = "temp: throwaway idea"
FINAL_BRANCHES = {"main", "feature/obstacle-avoidance", "feature/path-planning",
                  "hotfix/sensor-timeout", "experiment/detached-recovery"}


class GitError(RuntimeError):
    """Raised when the repository is not set up the way the grader expects."""


class Commit(NamedTuple):
    """A published commit."""

    sha: str
    author: str
    email: str
    subject: str


def run_git_rc(repo: str, *args: str) -> Tuple[int, str]:
    """Run git in 'repo' and return (exit code, stdout)."""
    env = dict(os.environ, LC_ALL="C", GIT_PAGER="cat", GIT_TERMINAL_PROMPT="0")
    proc = subprocess.run(["git", *args], cwd=repo, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout


def run_git(repo: str, *args: str) -> str:
    """Run git in 'repo' and return stdout ('' on failure)."""
    return run_git_rc(repo, *args)[1]


class Facts:
    """Everything the grader needs to know about the repository. Read-only: never changes the repo."""

    def __init__(self, repo: str) -> None:
        self.repo = repo
        if run_git_rc(repo, "rev-parse", "--verify", "-q", "origin/main^{commit}")[0] != 0:
            raise GitError("origin/main not found. Run the grader inside your clone of the lab repository "
                           "(a clone made with 'git clone ...').")
        raw = run_git(repo, "log", "origin/main", "--format=%H%x1f%an%x1f%ae%x1f%s")
        self.published: List[Commit] = [Commit(*line.split("\x1f")) for line in raw.splitlines() if line.strip()]
        self.origin_tip: str = self.published[0].sha
        self.release: str = self._sha_for(RELEASE_SUBJECT)
        self.baseline: str = self._sha_for(BASELINE_SUBJECT)

    def _sha_for(self, subject: str) -> str:
        for commit in self.published:
            if commit.subject == subject:
                return commit.sha
        raise GitError(f"published history has no commit with subject '{subject}'")

    # -- published history -------------------------------------------------------------
    def published_emails(self) -> Set[str]:
        """E-mail addresses of the people who wrote the published history."""
        return {c.email.lower() for c in self.published}

    def published_names(self) -> Set[str]:
        """Names of the people who wrote the published history."""
        return {c.author.lower() for c in self.published}

    # -- the student's live repository -------------------------------------------------
    def config_value(self, key: str) -> str:
        """Value of a repository-local config key ('' if unset)."""
        return run_git(self.repo, "config", "--local", "--get", key).strip()

    def local_branches(self) -> Dict[str, str]:
        """{branch name: full SHA} for refs/heads."""
        out = run_git(self.repo, "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads")
        return dict(line.split() for line in out.splitlines() if line.strip())

    def rev(self, ref: str) -> str:
        """Full SHA of 'ref' ('' if it does not name a commit)."""
        return run_git(self.repo, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}").strip()

    def commit_exists(self, token: str) -> bool:
        """True if 'token' names a commit object in this repository."""
        return run_git_rc(self.repo, "cat-file", "-e", f"{token}^{{commit}}")[0] == 0

    def subject_of(self, token: str) -> str:
        """Subject line of the commit named by 'token' ('' if unknown)."""
        return run_git(self.repo, "show", "-s", "--format=%s", token).strip()

    def parent(self, sha: str) -> str:
        """Full SHA of the first parent of 'sha' ('' for a root commit)."""
        return self.rev(f"{sha}^")

    def commits_above(self, base: str, tip: str) -> List[Dict[str, object]]:
        """Commits in base..tip, oldest first: sha, subject, files (all touched), added (new files)."""
        out = run_git(self.repo, "rev-list", "--reverse", f"{base}..{tip}")
        commits: List[Dict[str, object]] = []
        for sha in out.split():
            tree = ("diff-tree", "--no-commit-id", "--name-only", "-r")
            commits.append({
                "sha": sha,
                "subject": self.subject_of(sha),
                "files": run_git(self.repo, *tree, sha).split(),
                "added": run_git(self.repo, *tree, "--diff-filter=A", sha).split(),
            })
        return commits

    def file_at(self, ref: str, path: str) -> Optional[str]:
        """Content of 'path' at 'ref' (None if absent)."""
        code, out = run_git_rc(self.repo, "show", f"{ref}:{path}")
        return out if code == 0 else None

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """True if commit 'ancestor' is 'descendant' itself or part of its history."""
        return run_git_rc(self.repo, "merge-base", "--is-ancestor", ancestor, descendant)[0] == 0

    def contained_in_any_branch(self, sha: str) -> bool:
        """True if some local or remote branch contains commit 'sha'."""
        return bool(run_git(self.repo, "branch", "-a", "--contains", sha).strip())

    def head_reflog(self) -> List[Dict[str, str]]:
        """HEAD reflog, newest first: [{'sha': ..., 'msg': ...}]."""
        out = run_git(self.repo, "log", "-g", "--format=%H%x1f%gs", "HEAD")
        entries = []
        for line in out.splitlines():
            sha, _, msg = line.partition("\x1f")
            entries.append({"sha": sha, "msg": msg})
        return entries

    def reflog_commit(self, subject: str) -> Optional[str]:
        """Full SHA of the commit made with this subject, found in the HEAD reflog (None if absent)."""
        for entry in self.head_reflog():
            if entry["msg"] == f"commit: {subject}":
                return entry["sha"]
        return None

    def c_test_passes(self, ref: str) -> bool:
        """Export 'ref' to a temporary folder and run its tests/check_build.py there.

        Raises RuntimeError with one readable sentence when the C code cannot be built (no compiler)."""
        archive = subprocess.run(["git", "archive", "--format=tar", ref], cwd=self.repo,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if archive.returncode != 0:
            raise RuntimeError(f"could not export {ref}")
        with tempfile.TemporaryDirectory() as tree:
            subprocess.run(["tar", "-x", "-C", tree], input=archive.stdout, check=True)
            proc = subprocess.run([sys.executable, os.path.join(tree, "tests", "check_build.py")], cwd=tree,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8",
                                  errors="replace", env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if proc.returncode == 2:
            lines = proc.stdout.strip().splitlines()
            raise RuntimeError(lines[-1] if lines else "the C test could not be built")
        return proc.returncode == 0 and "ALL TESTS PASSED" in proc.stdout
