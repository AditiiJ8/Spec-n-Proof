# spec-and-proof

Two [Agent Skills](https://agentskills.io/specification) for AI coding agents.

- **spec-sprint** turns a vague idea into a short specification (`SPEC.md`) and an ordered task plan (`PLAN.md`) before any code is written.
- **proof-build** implements one task at a time, runs the checks that exist, and reports each one as `PASS`, `FAIL`, `NOT RUN`, or `BLOCKED`. It never claims a result it did not observe.

```
idea -> SPEC.md -> PLAN.md -> one task -> tests -> evidence-based report
        (spec-sprint)                     (proof-build)
```

Each skill works alone. Together they share one small contract: tasks in `PLAN.md` have a "Done when" condition and a "Verify with" check, and proof-build reads them.

## The problem

Coding agents fail in two repeatable ways. They start building before the goal is clear, so the first hour goes to the wrong thing. And they finish with "all tests pass" when they ran nothing, ran something unrelated, or changed the tests until they went green.

These skills are plain Markdown instructions aimed at those two failures. There is no runtime, no API key, no network call, and no model call anywhere in the repository.

## Repository layout

```
skills/
  spec-sprint/
    SKILL.md
    assets/SPEC.template.md, PLAN.template.md
  proof-build/
    SKILL.md
    assets/REPORT.template.md
examples/
  sample-project-idea.md          a vague request
  sample-spec.md, sample-plan.md  what spec-sprint output looks like
  expense-tracker/                the small program the plan describes, with 20 tests
  sample-verification-report.md   what proof-build output looks like
tests/
  validate_skills.py              checks skills against the Agent Skills spec
  test_skill_structure.py         unit tests (validator, skills, examples, links)
DEMO.md                           a five-minute walkthrough
```

The only addition to the minimal layout is `assets/`, which the specification defines for templates. Agents load those files when needed, so each `SKILL.md` stays short.

## Install

A skill is a folder whose name matches the `name` in its `SKILL.md`. Copy the whole folder, because the templates in `assets/` travel with it. Each skill is self-contained, so you can install one without the other.

Claude Code, for all your projects:

```bash
mkdir -p ~/.claude/skills
cp -r skills/spec-sprint ~/.claude/skills/
cp -r skills/proof-build ~/.claude/skills/
```

Claude Code, for one project only (commit it and your team gets it too):

```bash
mkdir -p .claude/skills
cp -r skills/spec-sprint .claude/skills/
cp -r skills/proof-build .claude/skills/
```

Those two locations come from [Claude Code's skills documentation](https://code.claude.com/docs/en/skills). If the skills directory did not exist when your session started, restart Claude Code once so it can watch the new directory.

Other tools: the folders follow the open Agent Skills format, so any client that implements it should accept them. Copy them to the directory that client scans and check its documentation for the path. This repository makes no compatibility claim about any client other than Claude Code, and it has not been run inside a live agent session.

## Use

Ask in plain language. The `description` in each `SKILL.md` is what lets an agent pick the skill up on its own.

```
Use spec-sprint on this idea: "I keep losing track of what I spend..."
```

```
Use proof-build to do the next unchecked task in PLAN.md.
```

In Claude Code, a skill's name also works as a slash command, so `/spec-sprint` and `/proof-build` are available too, per its documentation.

## Validate

Python 3 and nothing else.

```bash
python3 -m unittest discover -s tests -v     # structural tests
python3 tests/validate_skills.py             # prints [OK] or [FAIL] per skill
python3 -m unittest discover -s examples/expense-tracker -v   # the demo program's own 20 tests
```

What the structural tests check:

- both `SKILL.md` files exist, with valid frontmatter, a valid `name` that matches its folder, and a non-empty `description` under 1024 characters
- no unknown frontmatter fields, and quoted strings where YAML would otherwise read a number
- every workflow stage appears as a heading, in order, plus key phrases such as the four status words
- every relative file reference resolves and stays inside its skill folder
- the two skills agree on the plan format and the status vocabulary
- the validator rejects bad input (uppercase names, hyphen rules, wrong folder name, broken links, and so on), so a passing run means something
- the examples exist, and links in the README, DEMO, and examples resolve

The rules come from the specification page at agentskills.io, which was read while building this. The project's own validator is a lightweight stand-in for the official `skills-ref` library, which is the authority.

To cross-check against the official library (needs network access, so it is not part of the test suite):

```bash
python3 -m venv /tmp/refenv
/tmp/refenv/bin/pip install "git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
/tmp/refenv/bin/skills-ref validate skills/spec-sprint
/tmp/refenv/bin/skills-ref validate skills/proof-build
```

Both skills passed this check on 2026-10-03, and a deliberately broken copy failed it.

## What the tests do not cover

Passing tests mean the files are well formed and consistent. They do not show that an agent follows the instructions well, that the instructions improve results, or that the skills are production-ready. Nobody has measured that yet. The honest way to test it is to run an agent on real tasks with and without the skills and compare. That has not been done.

## Design choices

- Two skills, not one, because planning and building are different moments with different failure modes. A shared plan format connects them.
- Four status words, because "not checked" and "could not check" are different facts and a report should not blur them.
- Approval gates in the instructions. proof-build does not commit, push, deploy, or delete without the user's say-so, and spec-sprint never overwrites an existing `SPEC.md` or `PLAN.md`.
- Questions are capped at three, each with a default, so planning cannot stall on a user who wants to move.
- The demo program is real and small, so the sample report contains captured results instead of invented ones.

## Limitations

- The instructions are tested for structure only, as described above. Agent behavior is unmeasured.
- The frontmatter parser reads the small YAML subset the specification uses. It rejects anything else instead of guessing, so a valid but unusual YAML file could be flagged.
- Name characters are checked with Python's `isalnum` and `lower`. The official library may treat unusual Unicode letters differently.
- The demo program and its tests were run on Linux with Python 3.12.3 only.
- The sample spec, plan, and report are examples written by hand. Only the commands and outputs listed in the report were captured from real runs.
- The `skills-ref` cross-check was run once, at build time. Later edits to the skills need a rerun.

## Attribution and license

Released under the [MIT License](LICENSE).

This project was written independently. It shares a general idea with [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills), which was suggested as inspiration: agent workflows that specify first, work in small steps, and verify. No text or code from that project is used here, and this project is not affiliated with it. The file format follows the public [Agent Skills specification](https://agentskills.io/specification).
