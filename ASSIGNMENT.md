# Git Lab Assignment: Kestrel-1 Rover, One Shift of Branching

**Course:** 26RA2308 Git for Software Development and Collaboration
**Builds on:** Experiments 1 to 6. **Based on:** Experiment 7 (Branch Creation and Switching)
**Time allowed:** 1 hour 30 minutes. **Marks:** 100

---

## The story

It is 09:00 on a Monday at the Kestrel-1 rover lab and you are the new teammate. **Asha** writes the C
firmware, **Ben** plans the routes and cuts the releases, **Chitra** tunes the camera detector. Release
`v0.1` is already out in the field. The lab has one rule:

> **`main` holds only reviewed work, so everything new starts on a branch.**

Your shift ends at 10:30. Between now and then you will open work streams, write two features side by
side, tidy up, fix a bug in the released version, and rerun an old experiment. Every command is a
command from Experiment 7: `git branch`, `git switch`, `git checkout`, `git commit -a`, `git log --graph`,
`git branch -m / -d / -D`, branching from an old commit, and detached HEAD. Along the way you reuse
`git config` and aliases (Experiment 3), `git add` and `git commit` (Experiments 4 and 5), `git log`,
`git diff`, `git status` and `git reflog` (Experiment 6) and the terminal skills from Experiments 1 and 2
(`cat`, `ls`, `head`, `wc`).

## What you need

`git` (version 2.23 or newer, for `git switch`), `python3`, `nano`, and a C compiler (`gcc` or `cc`).
Check with `git --version && python3 --version && gcc --version`. If your terminal does not print English
messages, run `export LC_ALL=C` first, because the grader reads what Git prints. If a long output opens in
a pager (a screen with `:` or `(END)` at the bottom), press `q` to leave it.

## How to edit a file with nano

Every file change in this lab is done in the `nano` editor. Never use `echo` to write into a file.

1. `nano <file>` opens the file (a new file is created when you save).
2. The cursor starts at the **top** of the file. Type exactly the text shown, pressing `Enter` between
   the lines. Do **not** press `Enter` after the last line: nano ends the file with a line break by itself.
3. Save with `Ctrl+O` and then `Enter` (that confirms the file name).
4. Leave with `Ctrl+X`.

If nano says "Save modified buffer?", press `Y` and then `Enter`. If you typed into the wrong file, press
`Ctrl+X`, then `N`, and start again. Whenever the text shows `Your Full Name`, type your own name, exactly
as in `git config user.name`.

## Rules

1. Work **only inside your own clone**. Do not push anything (`git push` is not part of this lab).
2. Do not use `git merge`, `git rebase` or `git reset` (merging is Experiment 8). Never commit on `main`.
3. Type the commands yourself. The grader checks that your pasted output matches what is really in your
   repository, so output copied from a classmate is detected.
4. Keep the commit messages exactly as written.
5. **Files come and go when you switch.** `ASSIGNMENT.md` and `tests/grade.py` exist only on `main` and
   on branches made from its latest commit. When you stand on an old commit (Tasks 6 and 7) they
   disappear from the folder, and they come back when you return to `main`. Run the grader from `main`.
   While you stand on an old commit, change only the files a task tells you to (read this handout from the
   PDF or from GitHub, not from the folder), or Git may refuse to switch back to `main`.

## How you hand in your work

1. In Task 1 you copy `submission/outputs.template.txt` to `submission/outputs.txt`.
2. After **each step** (they are numbered **1.1**, **1.2**, ...), paste what the terminal printed under
   the matching `--- N.M` line of `submission/outputs.txt`, replacing `(paste output here)`. Do not edit
   or delete the `=== TASK` and `--- N.M` lines. Type your answers after the colon of the `ANSWER-n :` lines
   (the line just below each `# Qn` question). Any editor is fine for `submission/outputs.txt`, for example a
   second terminal with nano, or VS Code: the nano rule is for the project files.
3. Fill in your name and registration number at the top of the file.
4. Run the automatic grader whenever you want to see where you stand (from branch `main`):

   ```bash
   python3 tests/grade.py
   ```

   It prints **PASS** or **FAIL** for every task, tells you exactly which check failed, and shows your
   score out of 100. You can fix a mistake and run it again as often as you like.
5. When you are done, show the final grader output to your instructor (it is also saved in
   `submission/results.txt`), and submit `submission/outputs.txt` as instructed.

## Time plan

| Task | Time on the clock | Topic | Suggested time | Marks |
|---|---|---|---|---|
| 1 | 09:00 | Arrive and look around | 8 min | 10 |
| 2 | 09:10 | Open work streams | 8 min | 15 |
| 3 | 09:20 | Two features in parallel | 14 min | 20 |
| 4 | 09:35 | The big picture | 6 min | 10 |
| 5 | 09:40 | Tidy up | 7 min | 10 |
| 6 | 09:50 | Hotfix from the release commit | 12 min | 15 |
| 7 | 10:05 | Detached HEAD | 12 min | 15 |
| 8 | 10:20 | Shift summary | 3 min | 5 |
| | | Buffer for running the grader and fixing mistakes | 20 min | |

---

## Task 1: Arrive and look around (10 marks)

Get your own copy of the project, tell Git who you are, and look around before you touch anything. Which
branch are you on? Where does Git write that down? A branch should be a very small thing: find out how
small.

```bash
git clone https://github.com/qbit-glitch/26RA2308-gitlab-7-rover-branching-lab.git rover-branching-lab
cd rover-branching-lab
cp submission/outputs.template.txt submission/outputs.txt
git config user.name "Your Full Name"
git config user.email "your.email@example.com"
git config alias.tree "log --oneline --graph --decorate --all"
```

Use your own real name and e-mail (not the placeholders above, and not one of the teammates'). Do **not**
use `--global` here. Your instructor may give you a different clone URL.

* **1.1** Run `git config --local --list` and paste the output.
* **1.2** Run `git branch -v` and paste the output. One branch, and the `*` shows it is checked out.
* **1.3** Run `git branch -a` and paste the output. The names starting with `remotes/` are Git's memory of
  the shared copy.
* **1.4** Git keeps the current branch name in `HEAD` and each branch in a tiny file. Run this and paste the
  three lines it prints (the last one is the file size in bytes):

  ```bash
  cat .git/HEAD && cat .git/refs/heads/main && wc -c < .git/refs/heads/main
  ```

## Task 2: Open work streams (15 marks)

Three people need you at once, and you have an idea of your own. Open a work stream for each, using each
way Git offers to make a branch. A new branch starts at the commit you are standing on, and you have not
committed anything yet, so all of them start at the tip of `main`.

```bash
git branch feature/obstacle-avoidance
git switch feature/obstacle-avoidance
```

* **2.1** Paste the output of the `git switch` command (`git branch` alone prints nothing).

```bash
git switch -c feature/path-planning
```

* **2.2** Paste the output.

```bash
git checkout -b experiment/yolo-baseline
```

* **2.3** Paste the output.

```bash
git checkout -b feature/discarded-idea
```

* **2.4** Paste the output.

You are now on `feature/discarded-idea`. Write down the idea in a new file. Open it in nano:

```bash
nano IDEAS.txt
```

Type this one line, then `Ctrl+O`, `Enter`, `Ctrl+X`:

```text
Idea: try a lidar instead of the ultrasonic sensor - Your Full Name
```

Commit it, so that this branch holds work of its own:

```bash
git add IDEAS.txt
git commit -m "wip: try lidar for obstacle detection"
```

* **2.5** Paste the output of the `git commit` command.

```bash
git checkout main
git branch -v
```

* **2.6** Paste the output of both commands. Look at the commit numbers: three of the new branches sit on
  the same commit as `main`, one is a commit ahead.

## Task 3: Two features in parallel (20 marks)

Asha wants an obstacle-avoidance stub and Ben wants a path-planner stub. Write them side by side on two
branches. Then walk between the branches and watch the files appear and disappear: nothing leaks from one
to the other.

Start with Asha's feature, which edits a file that already exists:

```bash
git switch feature/obstacle-avoidance
nano src/controller.c
```

At the top of the file type these two lines, then press `Enter` **twice** after the second one (the extra
`Enter` leaves an empty line before the old first line), then save and exit:

```text
/* obstacle avoidance stub - Your Full Name */
void avoid(void) { }
```

Because `controller.c` is already tracked, `git commit -a` can stage and commit it in one go:

```bash
git commit -am "feat(nav): add obstacle avoidance stub"
```

* **3.1** Paste the output of the commit.

Now Ben's feature, which is a brand-new file:

```bash
git switch feature/path-planning
nano tools/planner.py
```

Type these three lines (the last one starts with four spaces), then save and exit:

```text
# Path planner stub - Your Full Name
def plan():
    pass
```

A new file is not tracked, so `-a` would skip it. Add it first:

```bash
git add tools/planner.py
git commit -m "feat(nav): add path planner stub"
```

* **3.2** Paste the output of the commit (look for `create mode`).

Now visit each branch and look at what is in the folder:

```bash
git switch feature/obstacle-avoidance
ls tools
head -3 src/controller.c
```

* **3.3** Paste the output of all three commands.

```bash
git switch feature/path-planning
ls tools
head -3 src/controller.c
```

* **3.4** Paste the output of all three commands.

```bash
git switch main
ls tools
head -3 src/controller.c
```

* **3.5** Paste the output of all three commands.

```bash
git diff --stat feature/obstacle-avoidance feature/path-planning
```

* **3.6** Paste the output.

## Task 4: The big picture (10 marks)

Ben leans over: "Where is everybody's work?" Draw him the picture, and list what is already part of `main`
and what is not. Stay on `main`.

* **4.1** Run `git tree` (your alias from Task 1) and paste the output. Find the point where the history forks.
* **4.2** Run `git branch -a` and paste the output.
* **4.3** Run `git branch --merged` and paste the output (branches whose work is already in the branch you
  are on).
* **4.4** Run `git branch --no-merged` and paste the output.
* Then type your answer to `ANSWER-1` in the file (there is no pasted output for it): how many of your
  branches contain work that `main` does not have?

## Task 5: Tidy up (10 marks)

Chitra asks you to name the model baseline after the model version, and the lidar idea is dead. Rename one
branch, remove the finished one the safe way, and remove the dead one the forced way. Git will refuse the
first attempt: read why. You must be on `main` (you are).

```bash
git branch -m experiment/yolo-baseline experiment/yolov8-baseline
git branch
```

* **5.1** Paste the output of `git branch`. The old name is gone.

```bash
git reflog experiment/yolov8-baseline
```

* **5.2** Paste the output. A branch has its own little history, and it recorded the rename.

```bash
git branch -d experiment/yolov8-baseline
```

* **5.3** Paste the output. This branch has no work that `main` lacks, so the safe delete is allowed.

```bash
git branch -d feature/discarded-idea
```

* **5.4** Paste the output. Git refuses: the branch holds a commit that is nowhere else.

```bash
git branch -D feature/discarded-idea
```

* **5.5** Paste the output. The capital `-D` says "I am sure". Note the number after `was`: it is the commit
  that is now on no branch.

```bash
git branch -v
```

* **5.6** Paste the output.

## Task 6: Hotfix from the release commit (15 marks)

The field team calls: the `v0.1` rover freezes when an obstacle is more than about 85 cm away. `main` already
holds unfinished work from this week, so Ben says: "Fix it from the release itself." Find the release
commit, branch from it, watch the test fail, fix one number, watch it pass.

```bash
git log --oneline
```

* **6.1** Paste the output. Find the line `release: v0.1 field build`, copy its number and type it as
  `ANSWER-2` in the file.

Now make a branch that starts at that commit, and look at where you are:

```bash
git switch -c hotfix/sensor-timeout <SHA of ANSWER-2>
git log --oneline -1
```

* **6.2** Paste the output of both commands. The folder now looks the way it did on release day (remember
  rule 5).

```bash
python3 tests/check_build.py
```

* **6.3** Paste the output. It is **supposed to fail**: the far-object case reads "no echo" because the
  timeout is far too short.

The timeout is the number on the first line of `src/sensor_limits.h`. It is `5` and should be `50`:

```bash
nano src/sensor_limits.h
```

Press `Ctrl+E` to jump to the end of the first line, type `0` (so `5` becomes `50`), then save and exit.

```bash
git diff
```

* **6.4** Paste the output. You should see one line removed and one added.

```bash
python3 tests/check_build.py
```

* **6.5** Paste the output. It must end with `ALL TESTS PASSED`.

```bash
git commit -am "fix(sensor): raise echo timeout to 50 ms"
```

* **6.6** Paste the output.

```bash
git tree
```

* **6.7** Paste the output. Your hotfix branches off the release commit, behind the unfinished work on `main`.

## Task 7: Detached HEAD (15 marks)

Chitra needs last month's baseline number. Check out the old commit directly and run the detector. Commits
made there belong to no branch, so save your notes on a branch before you leave. Then try a second idea and
leave it behind on purpose, and read what Git tells you as you walk away.

```bash
git switch main
git log --oneline -- results/experiments.txt
```

* **7.1** Paste the output of the `git log` command. Find the line `experiment: baseline detector run at
  threshold 0.40`, copy its number and type it as `ANSWER-3` in the file.

```bash
git checkout <SHA of ANSWER-3>
```

* **7.2** Paste the output. Read Git's warning about the "detached HEAD" state.

```bash
python3 tools/detector.py data/readings.txt
git status
```

* **7.3** Paste the output of both commands. The detector reproduces the logged number.

Write your result down:

```bash
nano results/notes.txt
```

Type this one line, then save and exit:

```text
Reproduced the baseline: accuracy 0.750 - Your Full Name
```

```bash
git add results/notes.txt
git commit -m "temp: experiment from old commit"
```

* **7.4** Paste the output of the commit. The number in the square brackets is the new commit; type it as
  `ANSWER-4`. It belongs to no branch yet.

Save it before it can be lost:

```bash
git switch -c experiment/detached-recovery
git log --oneline -2
```

* **7.5** Paste the output of both commands.

Now a second attempt, which you will abandon. Go back to the old commit, write one line, commit it:

```bash
git checkout <SHA of ANSWER-3>
nano results/scratch.txt
```

Type this one line, then save and exit:

```text
Idea: try threshold 0.55 - Your Full Name
```

```bash
git add results/scratch.txt
git commit -m "temp: throwaway idea"
```

* **7.6** Paste the output of the commit.

Walk away without saving it:

```bash
git switch main
git reflog -6
```

* **7.7** Paste the output of both commands. Read the warning about "leaving 1 commit behind". The reflog
  still remembers the commit, but it is on no branch.

## Task 8: Shift summary (5 marks)

Show the final picture of your shift. You should be on `main`.

```bash
git branch -vv
```

* **8.1** Paste the output.

```bash
git status
```

* **8.2** Paste the output. `main` must be exactly where it was when you started.
* Then type your answer to `ANSWER-5` in the file: how many local branches do you have now?

## Finish

```bash
python3 tests/grade.py
```

You want to see `PASS` for all eight tasks and `TOTAL: 100/100`. Anything marked `FAIL` is listed with the
reason; fix it and run the grader again. Run it from `main`.

## Marks

| Task | Marks | How it is checked |
|---|---|---|
| 1 | 10 | your pasted config matches the repository's real configuration; the branch listings and the 41-byte file are right |
| 2 | 15 | the messages and listings are right; the idea commit really sits on the starting commit; the reflog shows you moved between the branches |
| 3 | 20 | each branch holds exactly its own commit and file, signed with your name; the pasted listings differ per branch |
| 4 | 10 | the graph and the three branch lists match; one answer |
| 5 | 10 | the rename is in the branch reflog; `-d` was refused; the deleted commit still exists but no branch has it |
| 6 | 15 | the hotfix is one commit on the release commit, changes only the timeout, and the test passes there |
| 7 | 15 | the rescue branch holds your note on the old commit; the abandoned commit exists on no branch; Git's warning is pasted |
| 8 | 5 | exactly five local branches, and `main` is unchanged |

A task shows **PASS** only when every check in it passes, and you earn marks for each check that passes
even if the task as a whole fails.

## If something goes wrong

* **Nothing printed / wrong branch.** Run `git status` and `git branch` and read them. The branch with the `*` is the one you are on.
* **`nothing to commit` after a nano edit.** You probably did not save: reopen the file and use `Ctrl+O`, `Enter`, `Ctrl+X`. Or the file is new and needs `git add` first.
* **You typed into the wrong file.** `Ctrl+X`, then `N` throws the change away. If you already saved, open the file again and delete your lines.
* **`git switch` says your changes would be overwritten.** Commit your work first, then switch.
* **A typo in a branch name.** `git branch -m wrong-name right-name` renames it.
* **A commit landed on `main` by mistake.** Do not try to undo it with `reset` (it is not allowed here). Tell your instructor; the grader will show it in Task 8.
* **`python3 tests/check_build.py` says no C compiler.** Use a lab machine, or install `build-essential` (Ubuntu) or the Xcode command line tools (macOS).
* **`tests/grade.py` or `ASSIGNMENT.md` is missing.** You are standing on an old commit. Run `git switch main`.
* **You made a mistake early on.** `git reflog` shows everything `HEAD` did. If the repository is beyond repair, delete the folder, clone again and redo the tasks (your pasted outputs must be produced in the new clone).
