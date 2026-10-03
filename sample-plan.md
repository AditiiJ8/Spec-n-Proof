# PLAN: expense tracker

Spec: [sample-spec.md](sample-spec.md) (in a real project this would be SPEC.md)
MVP: A person can add expenses from the terminal, list them, and see totals by category.

> Example plan written by hand to show the shape SpecSprint produces. Tasks above "Later" are the MVP. The boxes are ticked because the program in [expense-tracker/](expense-tracker/) exists and its tests were run, as recorded in [the sample report](sample-verification-report.md).

## Tasks

- [x] T1: Amount parsing and formatting
  - Size: small, one sitting
  - Depends on: none
  - Done when: `parse_amount` turns valid text into integer cents and rejects the invalid cases in AC2, including more than two decimal places such as `1.005`. `format_amount` prints cents with two decimals.
  - Verify with: `python3 -m unittest discover -s examples/expense-tracker -v` (ParseAmountTests, FormatAmountTests)
  - Covers: AC2, AC6

- [x] T2: Storage that cannot corrupt data
  - Size: small, one sitting
  - Depends on: none
  - Done when: a missing file loads as empty, a damaged file raises a clear error without being modified, and saving is atomic.
  - Verify with: the same command (StorageTests)
  - Covers: AC5

- [x] T3: The `add` command, through the command line
  - Size: small, one sitting
  - Depends on: T1, T2
  - Done when: `add 12.50 food "lunch"` stores a normalised record, and invalid input exits 1 without touching the file.
  - Verify with: the same command (AddTests, CliTests), then a manual run of `add` against a temporary file
  - Covers: AC1, AC2

- [x] T4: The `list` command
  - Size: small, one sitting
  - Depends on: T3
  - Done when: output matches AC3, including the empty case.
  - Verify with: the same command (CliTests), then a manual run of `list`
  - Covers: AC3

- [x] T5: The `total` command
  - Size: small, one sitting
  - Depends on: T3
  - Done when: totals and category totals match AC4, and three additions of 0.10 total 0.30.
  - Verify with: the same command (CliTests), then a manual run of `total`
  - Covers: AC4, AC6

## Later

Not part of the MVP. Do not start these without the user's go-ahead.

- Edit and delete commands
- Monthly summary
- CSV export
