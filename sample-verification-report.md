# Verification report: T1 to T5, expense tracker demo

Date: 2026-10-03
Environment: Linux 6.18.44-fc-v64, Python 3.12.3
Repo state at start: no git repository, empty `expense-tracker/` directory

## Where this report comes from

Read this first, because it separates what was observed from what is example content.

- Observed: every command, output line, and count in the Checks table was captured from commands run in the session that built this repository, on the date above. Nothing in the table is typed from memory.
- Example content: the program under `expense-tracker/` and this report were written by hand in that same session, following the proof-build steps (tests first, then code, then checks). This is not a recording of an agent invoking the skill. It shows the report format.
- Not shown here: any result from a different machine, Python version, or operating system.

## Result

All five plan tasks have their "Verify with" checks at PASS. 3 PASS, 0 FAIL, 1 NOT RUN, 1 BLOCKED in the table below.

## Baseline (before implementation)

The tests were written before `expenses.py` existed. Running them gave the expected failure:

- Command: `python3 -m unittest discover -s examples/expense-tracker`
- Observed: `ModuleNotFoundError: No module named 'expenses'`, then `Ran 1 test in 0.000s` and `FAILED (errors=1)`.
- Meaning: the failure was the missing module, which is the reason the tests were meant to fail. No assertion had run yet.

## Checks

| # | Check | Status | Command | Evidence |
|---|-------|--------|---------|----------|
| 1 | Unit tests for T1 to T5 (20 tests) | PASS | `python3 -m unittest discover -s examples/expense-tracker -v` | `Ran 20 tests in 0.025s`, `OK`, exit status 0 |
| 2 | Command-line smoke run covering AC1 to AC4 | PASS | `expenses.py add`, `list`, `total` against a temporary data file (full list below) | Totals and error lines matched the spec, see below |
| 3 | Secret scan of the example code | PASS | `grep -rniE "(api[_-]?key\|secret\|token\|passw(or)?d\|bearer\|AKIA[0-9A-Z]{8,})" examples/expense-tracker --include=*.py` | No matches (grep exit status 1) |
| 4 | Lint and style check | NOT RUN | none | No linter is configured for this demo, and none was installed |
| 5 | Run on Windows and on other Python versions | BLOCKED | none | Only Linux with Python 3.12.3 was available. Atomic file replacement and path handling are untested elsewhere |

Check 2, observed output (data file in a temporary directory, with `--date 2026-10-03` on the `add` calls):

```
$ expenses.py add 12.50 food "lunch"
Added 12.50 to food on 2026-10-03
$ expenses.py add 3 Travel "bus pass"
Added 3.00 to travel on 2026-10-03
$ expenses.py add 0.10 food "tea"
Added 0.10 to food on 2026-10-03
$ expenses.py list
2026-10-03       12.50  food  lunch
2026-10-03        3.00  travel  bus pass
2026-10-03        0.10  food  tea
$ expenses.py total
Total: 15.60
$ expenses.py total --category food
Total (food): 12.60
$ expenses.py add 1.005 food
error: too many decimal places: '1.005' (at most 2)      (exit status 1)
$ expenses.py add -5 food
error: not a valid amount: '-5' (use a positive number like 12.50)      (exit status 1)
```

## Changes

- `examples/expense-tracker/test_expenses.py`: 20 tests, written first.
- `examples/expense-tracker/expenses.py`: the program (parse, load, save, add, total, command line).

No existing test was edited or removed. No dependency was added.

## Not verified

- Behavior on Windows, macOS, or any Python other than 3.12.3.
- Concurrent writers. The spec lists this as out of scope, and no test covers it.
- Very large data files and performance.
- Lint and style conformance.
- The diff was not reviewed with `git diff` because the directory is not a git repository. The files were read by hand, and check 3 covered secrets only.

## Pre-existing problems, assumptions, follow-ups

- Pre-existing failures: none, because the directory was empty at the start.
- Follow-up: edit and delete commands are in the plan's "Later" list.
- Follow-up: if this grows, add a linter and a CI job so that checks 4 and 5 can run on every change.
