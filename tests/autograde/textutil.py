"""Helpers for reading the text a student pasted into submission/outputs.txt."""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, NamedTuple, Optional, Sequence, Set, Tuple

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
BOUNDARY_RE = re.compile(r"^(?:---\s*(\d+\.\d+)\b.*|===\s*TASK\b.*)$", re.MULTILINE)
HEX_TOKEN_RE = re.compile(r"\b[0-9a-fA-F]{7,40}\b")
LINE_SHA_RE = re.compile(r"^[\s*|\\/_]*([0-9a-fA-F]{7,40})\b(.*)$")
PLACEHOLDER = "(paste output here)"
MIN_SHA_LEN = 7

CC_SUBJECT_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|test|chore|perf|build|ci)(\([^)]+\))?!?: \S.*"
)


def normalise(text: str) -> str:
    """Remove colour codes and carriage returns and strip trailing blanks."""
    text = ANSI_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n"))


def parse_steps(text: str) -> Dict[str, str]:
    """Split the submission into {step id: pasted text}, e.g. {"2.3": "..."}."""
    steps: Dict[str, str] = {}
    matches = list(BOUNDARY_RE.finditer(text))
    for index, match in enumerate(matches):
        step_id = match.group(1)
        if step_id is None:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end]
        body = "\n".join(
            line for line in body.split("\n") if line.strip() != PLACEHOLDER
        ).strip("\n")
        steps[step_id] = (steps[step_id] + "\n" + body) if step_id in steps else body
    return steps


def header_field(text: str, label: str) -> str:
    """Return the value of a 'Label : value' line near the top of the file."""
    match = re.search(rf"^{label}\s*:[ \t]*(.*)$", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def get_answer(text: str, number: int) -> str:
    """Return the student's ANSWER-<number> value ('' if blank or a placeholder)."""
    match = re.search(rf"^ANSWER-{number}[ \t]*:[ \t]*(.*)$", text, re.MULTILINE)
    if not match:
        return ""
    value = match.group(1).strip().strip("`'\" ")
    return "" if value.startswith("<") else value


def get_answer_int(text: str, number: int) -> str:
    """The first whole number in the student's ANSWER-<number> ('3 branches' gives '3'; '' if none)."""
    match = re.search(r"\d+", get_answer(text, number))
    return match.group(0) if match else ""


def get_answer_sha(text: str, number: int) -> str:
    """The first commit number (7-40 hex digits) in the student's ANSWER-<number> ('' if none)."""
    match = re.search(r"\b[0-9a-fA-F]{7,40}\b", get_answer(text, number))
    return match.group(0).lower() if match else ""


def safe_text(text: str) -> str:
    """Remove control characters (ESC, BEL, newlines, ...) so student-written text cannot steer a terminal."""
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)


def all_shas(text: str) -> List[str]:
    """Every hex token of 7-40 characters anywhere in the text (lower case)."""
    return [token.lower() for token in HEX_TOKEN_RE.findall(text)]


def line_shas(text: str) -> List[str]:
    """The leading hex token of each line (works for --oneline and --graph output)."""
    found: List[str] = []
    for line in text.split("\n"):
        match = LINE_SHA_RE.match(line)
        if match:
            found.append(match.group(1).lower())
    return found


class OnelineEntry(NamedTuple):
    """One line of 'git log --oneline' output."""

    sha: str
    subject: str


def oneline_entries(text: str) -> List[OnelineEntry]:
    """Parse 'git log --oneline [--decorate --graph]' lines into entries."""
    entries: List[OnelineEntry] = []
    for line in text.split("\n"):
        match = LINE_SHA_RE.match(line)
        if match:
            entries.append(OnelineEntry(match.group(1).lower(), match.group(2).strip()))
    return entries


def strip_decoration(subject: str) -> str:
    """Drop a leading '(HEAD -> main, origin/main)' decoration from a --oneline subject."""
    return re.sub(r"^\([^)]*\)\s*", "", subject).strip()


def sha_matches(token: str, full_sha: str) -> bool:
    """True when 'token' is an abbreviation (>= 7 chars) of 'full_sha'."""
    token = token.lower().strip()
    return len(token) >= MIN_SHA_LEN and full_sha.lower().startswith(token)


def resolve(tokens: Iterable[str], full_shas: Sequence[str]) -> Tuple[Set[str], List[str]]:
    """Map abbreviated tokens onto known full SHAs; return (matched, unknown tokens)."""
    matched: Set[str] = set()
    unknown: List[str] = []
    for token in tokens:
        hits = [full for full in full_shas if sha_matches(token, full)]
        if hits:
            matched.add(hits[0])
        else:
            unknown.append(token)
    return matched, unknown


def sha_set_equals(text: str, expected: Sequence[str]) -> bool:
    """True if the lines of 'text' list exactly the expected commits (any order)."""
    matched, unknown = resolve(line_shas(text), expected)
    return matched == set(expected) and not unknown


class Status(NamedTuple):
    """The facts a pasted 'git status' (long format) tells us."""

    staged: Dict[str, str]
    unstaged: Dict[str, str]
    untracked: Set[str]
    clean: bool
    ahead: Optional[int]
    up_to_date: bool


_ENTRY_RE = re.compile(r"^(modified|new file|deleted|renamed|typechange):\s+(.*)$")


def parse_status(text: str) -> Status:
    """Parse the long form of 'git status' without depending on indentation."""
    staged: Dict[str, str] = {}
    unstaged: Dict[str, str] = {}
    untracked: Set[str] = set()
    mode: Optional[str] = None
    for raw in text.split("\n"):
        line = raw.strip()
        if line.startswith("Changes to be committed"):
            mode = "staged"
        elif line.startswith("Changes not staged for commit"):
            mode = "unstaged"
        elif line.startswith("Untracked files"):
            mode = "untracked"
        else:
            entry = _ENTRY_RE.match(line)
            if entry and mode in ("staged", "unstaged"):
                target = staged if mode == "staged" else unstaged
                target[entry.group(2).strip()] = entry.group(1)
            elif mode == "untracked" and line and not line.startswith("("):
                untracked.add(line)
    ahead = re.search(r"ahead of '[^']+' by (\d+) commit", text)
    return Status(
        staged=staged,
        unstaged=unstaged,
        untracked=untracked,
        clean="nothing to commit, working tree clean" in text,
        ahead=int(ahead.group(1)) if ahead else None,
        up_to_date=bool(re.search(r"up to date with '[^']+'", text)),
    )


PROMPT_ONLY_RE = re.compile(r"^.*[$%#>]$")


def last_nonblank_line(text: str) -> str:
    """The last line that is neither blank nor a bare shell prompt ('' if none)."""
    for line in reversed(text.split("\n")):
        stripped = line.strip()
        if stripped and not PROMPT_ONLY_RE.match(stripped):
            return stripped
    return ""


def parse_config_list(text: str) -> Dict[str, str]:
    """Parse 'git config --list' output into {key: value} (keys lower-cased)."""
    values: Dict[str, str] = {}
    for line in text.split("\n"):
        if "=" in line:
            key, _, value = line.partition("=")
            values[key.strip().lower()] = value.strip()
    return values


class BranchRow(NamedTuple):
    """One line of 'git branch' output."""

    current: bool
    name: str
    sha: str
    rest: str


_BRANCH_RE = re.compile(r"^(?P<cur>[* +]) (?P<name>\S+)(?: +(?P<sha>[0-9a-f]{7,40}))?(?: +(?P<rest>.*))?$")


# A row whose leading "* " or two spaces were lost when copying: a bare branch name, "name -> target", or
# "name <sha> subject". Git's message lines ("Switched to ...", "Your branch ...") and prompts do not match.
_BARE_RE = re.compile(r"^(?P<name>[^\s*+$#(\[][^\s]*)"
                      r"(?:\s+(?P<arrow>->\s+\S+)|\s+(?P<sha>[0-9a-f]{7,40})(?:\s+(?P<rest>.*))?)?$")


def parse_branch_list(text: str) -> List[BranchRow]:
    """Parse 'git branch [-v|-vv|-a|--merged|--no-merged]' output (also rows that lost their leading spaces)."""
    rows: List[BranchRow] = []
    for line in text.split("\n"):
        match = _BRANCH_RE.match(line.rstrip())
        if match is not None and match.group("name") not in ("$", "#"):
            rows.append(BranchRow(match.group("cur") == "*", match.group("name"),
                                  match.group("sha") or "", (match.group("rest") or "").strip()))
            continue
        bare = _BARE_RE.match(line.strip())
        if bare is not None:
            rows.append(BranchRow(False, bare.group("name"), bare.group("sha") or "",
                                  (bare.group("arrow") or bare.group("rest") or "").strip()))
    return rows


def branch_names(text: str) -> List[str]:
    """Branch names only, in the order printed."""
    return [row.name for row in parse_branch_list(text)]


def first_match(pattern: str, text: str) -> str:
    """The first whole match of 'pattern' in 'text' ('' if there is none)."""
    match = re.search(pattern, text)
    return match.group(0) if match else ""


def same_sha(a: str, b: str) -> bool:
    """True when two abbreviations (each at least 7 characters) name the same commit."""
    a, b = a.lower().strip(), b.lower().strip()
    return len(a) >= MIN_SHA_LEN and len(b) >= MIN_SHA_LEN and (a.startswith(b) or b.startswith(a))


_DECO_RE = re.compile(r"\(([^()]*)\)")


def decorations(text: str) -> Set[str]:
    """Every ref name shown in '--decorate' output ('HEAD -> main' gives HEAD and main; tags are skipped)."""
    names: Set[str] = set()
    for line in text.split("\n"):
        entry = LINE_SHA_RE.match(line)
        if not entry:
            continue
        deco = _DECO_RE.match(entry.group(2).strip())
        if not deco:
            continue
        for part in deco.group(1).split(","):
            part = part.strip()
            if part.startswith("tag:"):
                continue
            for piece in part.split(" -> "):
                names.add(piece.strip())
    return names
