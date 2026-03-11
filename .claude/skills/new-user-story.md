---
name: new-user-story
description: Use when creating a new user story for edh-deckbuilding-slots before beginning implementation of a new feature. Ensures consistent GitHub Issue format and correct US numbering.
---

# New User Story

A project-local skill for creating user stories as GitHub Issues on `StephenMeansMe/edh-deckbuilding-slots`.

## When to Use

Before any feature implementation. User stories must exist as closed GitHub Issues before work begins. If a feature request has no user story yet, create one now.

## Steps

### 1. Find the next US number

```bash
gh issue list --label user-story --state all --json number,title --jq '.[] | "\(.number) \(.title)"' | sort
```

Take the highest US-NNN number and add 1.

### 2. Draft the issue body

Use this format:

```markdown
## User Story

**As a/an** [role],
**I want** [goal],
**so that** [benefit].

## Background

[Why this is needed; link to related issues or roadmap items.]

## Acceptance Criteria

- [ ] ...
- [ ] ...

## Technical Notes

[Optional: constraints, edge cases, pointers to domain-concepts.md.]
```

### 3. Create the issue

```bash
gh issue create \
  --title "US-NNN: <short title>" \
  --label "user-story" \
  --body "$(cat <<'EOF'
[issue body here]
EOF
)"
```

Record the issue number GitHub assigns (e.g., `#56`).

### 4. Begin implementation

Reference the issue number in commits and PR descriptions. The issue stays **open** until the feature ships; close it with `gh issue close <N> --reason completed` as part of the PR merge step.

## Quick Reference

| Field | Convention |
|-------|-----------|
| Title | `US-NNN: <imperative phrase>` |
| Label | `user-story` |
| State at creation | open |
| State after ship | closed (reason: completed) |
| Body sections | User Story, Background, Acceptance Criteria, Technical Notes |

## Notes

- Read `docs/domain-concepts.md` before writing acceptance criteria for any story touching business logic.
- Acceptance criteria should be verifiable — prefer checkboxes (`- [ ]`) so shipped items can be checked off.
- The `Technical Notes` section is optional but encouraged for anything that constrains implementation (e.g., model-layer rules, save-format implications).
