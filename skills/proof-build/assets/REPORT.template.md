# Verification report: <task ID and title>

Date: <YYYY-MM-DD>
Environment: <OS and language or tool versions, as observed>
Repo state at start: <branch, and whether the working tree was clean>

## Result

<Two sentences. What changed, and how much of it is verified. Count the statuses, for example "N PASS, N FAIL, N NOT RUN, N BLOCKED".>

## Checks

| # | Check | Status | Command | Evidence |
|---|-------|--------|---------|----------|
| 1 | <what it checks> | <PASS, FAIL, NOT RUN, or BLOCKED> | `<exact command>` | <output lines you observed, or the reason for NOT RUN or BLOCKED> |

Status key: PASS means it ran and passed. FAIL means it ran and failed. NOT RUN means it was not executed (give the reason). BLOCKED means it could not be completed (give the reason and what would unblock it).

## Changes

- `<path>`: <what changed and why>

## Not verified

- <anything the checks above do not cover, or "Nothing known">

## Pre-existing problems, assumptions, follow-ups

- <item>
