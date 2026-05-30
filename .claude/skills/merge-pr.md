---
name: merge-pr
description: Use when merging a completed feature branch PR and cleaning up local main. Covers squash merge, local main reset, and the one sanctioned use of git reset --hard in this project.
---

# Merge PR

Use at the end of a feature branch, after CI passes and the PR is approved.

## When to Use

- A feature branch PR is ready to merge
- All required checks pass on GitHub
- You are on the feature branch (or `main` — the merge command works from either)

## Steps

### 1. Note the pre-session commit on main

Before merging, record the SHA that `main` pointed to at the start of this session. You need this for the reset step.

```bash
git log main --oneline | head -5   # find the SHA from before this session's work
```

### 2. Squash merge and delete the branch

```bash
gh pr merge <PR_NUMBER> --squash --delete-branch
```

This squashes all feature-branch commits into one on `main` and deletes the remote branch. The local feature branch is unaffected (you can delete it separately if needed).

### 3. Pull the squash commit

```bash
git checkout main
git pull
```

`main` now has exactly one new commit: the squash.

### 4. Reset local main to the pre-session state

```bash
git reset --hard <pre-session-sha>
```

This removes the squash commit from your **local** `main`, so your local `main` matches where it was before the session started. The squash commit still exists on `origin/main`.

**Why:** Feature work must live only on the squash commit on `origin/main`. A local `main` that includes the squash would confuse future sessions about what was done in this one.

## Safety Check

Confirm the reset target is correct before running it:

```bash
git log main --oneline | head -5   # verify <pre-session-sha> is shown
```

After the reset, `git status` should show a clean working tree and `git log main --oneline | head -1` should match the pre-session SHA.

## Notes

- `git reset --hard` is otherwise **categorically banned** in this project — this is the one sanctioned exception, and only for local `main` after a confirmed squash merge.
- If the PR had CI failures or was not actually merged, do not run the reset.
- If you are unsure of the pre-session SHA, check `git reflog main` to find the commit before the pull.
