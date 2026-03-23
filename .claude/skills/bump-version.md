---
name: bump-version
description: Use when releasing a new version of edh-deckbuilding-slots. Covers every location that must be updated so all version references stay in sync.
---

# Bump Version

Three sources must agree on the version number. Missing any one leaves the project in an inconsistent state.

## Checklist

**1. `pyproject.toml`** — the canonical package version:
```toml
version = "X.Y.Z"
```

**2. `CHANGELOG.md`** — add a new section above the previous release:
```markdown
## [X.Y.Z] — YYYY-MM-DD

### Added
...
```
Only include production changes (features, fixes, user-facing behaviour). Skip CI, docs-only, and project-management PRs.

**3. Git tag** — annotate the commit that updates the changelog:
```bash
git tag vX.Y.Z
```
The tag prefix is `v` (e.g. `v0.3.0`). Tag after committing the CHANGELOG update so the tag points at that commit.

## Order of Operations

```
1. Edit pyproject.toml   → version = "X.Y.Z"
2. Edit CHANGELOG.md     → add ## [X.Y.Z] entry
3. git add + git commit  → "docs: add CHANGELOG entry for vX.Y.Z"
4. git tag vX.Y.Z
```

## Verification

After tagging, confirm all three agree:

```bash
grep '^version' pyproject.toml          # version = "X.Y.Z"
head -10 CHANGELOG.md                   # ## [X.Y.Z] — ...
git tag --sort=-version:refname | head  # vX.Y.Z at top
```

## Semver Guidance

| Change type | Bump |
|-------------|------|
| New user-facing features | minor (0.X.0) |
| Bug fixes / small improvements | patch (0.0.X) |
| Breaking changes | major (X.0.0) |
