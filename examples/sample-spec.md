# SPEC: expense tracker

Status: example
Date: 2026-10-03

> This is an example of the shape SpecSprint produces for [the sample idea](sample-project-idea.md). It was written by hand for this repository, following the skill's template. It is not a recording of a live agent session.

## Problem

One person wants to record what they spend and see running totals without opening a full budgeting app. Today they remember amounts loosely or scroll through bank statements.

## Target users

A single person comfortable running a command in a terminal. No accounts, no sharing.

## Proposed solution

A command-line tool with three commands: `add`, `list`, and `total`. Data is stored in one local JSON file.

## Core features

- Add an expense with an amount, a category, and an optional note. The date defaults to today.
- List all expenses in the order they were added.
- Show the total of all expenses, or of one category.

## Non-goals

- Editing or deleting expenses. A user can edit the JSON file by hand for now.
- Multiple currencies, budgets, charts, or monthly reports.
- Syncing, import, export, or any network access.
- A graphical or web interface.

## Technical constraints

- Python 3 with the standard library only. Written and run on Python 3.12 only.
- Amounts are stored as integer cents so that repeated additions never drift.
- One data file: `--file PATH`, else `$EXPENSES_FILE`, else `./expenses.json`.
- Writes must not leave a half-written file behind.

## Assumptions

- A1: One currency, so amounts carry no currency symbol.
- A2: Categories are free text, compared case-insensitively.
- A3: At most two decimal places, and amounts must be greater than zero.
- A4: The user wants to be told about a damaged data file, not have it silently replaced.

## Acceptance criteria

- AC1: `add 12.50 food "lunch"` exits 0, prints a confirmation, and the data file then holds one record with `amount_cents` 1250.
- AC2: `add` with an invalid amount (`abc`, `0`, `-5`, `1.005`) exits 1, prints `error: ...` to stderr, and leaves the data file unchanged (or uncreated).
- AC3: `list` prints one line per expense (date, amount with two decimals, category, note) in insertion order. With no expenses it prints `No expenses yet.` and exits 0.
- AC4: `total` prints the sum of all expenses. `total --category food` prints the sum for that category, ignoring case. A category with no expenses totals `0.00`.
- AC5: A missing data file counts as empty. A data file that is not valid JSON, or not a list of expenses, makes every command exit 1 with an error and leaves the file untouched.
- AC6: Adding `0.10` three times gives a total of `0.30`.

## Risks and open questions

- Risk: a hand-edited data file with the wrong shape. Response: validate on load and refuse to write (AC5).
- Risk: two processes writing at once could lose an entry. Response: out of scope for a single-user tool. Noted here so nobody assumes otherwise.
- Question for the user: is editing or deleting needed soon? If yes, it moves from Later into the plan.
