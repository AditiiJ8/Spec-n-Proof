# Five-minute demo

You can run everything below without an API key. Steps 2 and 5 need an agent that supports Agent Skills. The rest run in a plain terminal.

Run all commands from the repository root.

## 1. Show the starting point (30 seconds)

Open [examples/sample-project-idea.md](examples/sample-project-idea.md). It is a loose request: no users, no platform, no definition of done. This is where agents usually guess and start coding.

## 2. Run spec-sprint (1 minute, needs an agent)

Install the skills ([README, Install](README.md#install)), then in an empty project folder ask:

```
Use spec-sprint on this idea: "I keep losing track of what I spend. I want something
simple where I can note down expenses and see how much I've spent. Maybe with
categories? It should be quick to use."
```

What to point out in the agent's response:

- at most three questions, each with a default (or stated assumptions if you tell it to just go)
- a `SPEC.md` with numbered, checkable acceptance criteria and a non-goals section
- a `PLAN.md` where every task has "Done when" and "Verify with", and an MVP line
- it asks before touching a `SPEC.md` that already exists

Compare with the reference result: [sample-spec.md](examples/sample-spec.md) and [sample-plan.md](examples/sample-plan.md). Your agent's output will differ in wording. The shape should match.

## 3. Show the program the plan describes (1 minute)

```bash
python3 -m unittest discover -s examples/expense-tracker -v
```

Expected: 20 tests, ending in `OK`.

```bash
export EXPENSES_FILE=$(mktemp -d)/demo.json
python3 examples/expense-tracker/expenses.py add 12.50 food "lunch"
python3 examples/expense-tracker/expenses.py add 3 travel "bus pass"
python3 examples/expense-tracker/expenses.py list
python3 examples/expense-tracker/expenses.py total --category food
python3 examples/expense-tracker/expenses.py add 1.005 food    # rejected, exit status 1
```

## 4. Show the report format (30 seconds)

Open [examples/sample-verification-report.md](examples/sample-verification-report.md). Point at three things:

- the "Where this report comes from" section, which says what was observed and what is example content
- the status table, where one check is `NOT RUN` and one is `BLOCKED` with a reason
- the "Not verified" section, which is mandatory

## 5. Run proof-build (1 minute, needs an agent)

In a project that has a `PLAN.md`:

```
Use proof-build to do the next unchecked task in PLAN.md.
```

What to point out:

- it reads the repo and finds the real test command before editing
- it states the task's "Done when" and "Verify with" first
- it writes or finds the test first and runs it
- it asks before anything destructive, and it does not commit
- the final report uses only `PASS`, `FAIL`, `NOT RUN`, `BLOCKED`, with the command and observed output beside each

## 6. Show that the validator can fail (1 minute)

```bash
python3 tests/validate_skills.py
```

Expected:

```
[OK] proof-build
[OK] spec-sprint
```

Now break a copy on purpose:

```bash
rm -rf /tmp/skills-broken && cp -r skills /tmp/skills-broken
sed -i 's/^name: spec-sprint/name: Spec-Sprint/' /tmp/skills-broken/spec-sprint/SKILL.md
sed -i 's/^## 6. Fix failures/## 6. Keep going/' /tmp/skills-broken/proof-build/SKILL.md
python3 tests/validate_skills.py /tmp/skills-broken
```

Expected: both skills report `[FAIL]` and the command exits with status 1. On macOS, use `sed -i ''` instead of `sed -i`.

Finish with the full suite:

```bash
python3 -m unittest discover -s tests -v
```

## Be upfront about

If a judge asks whether the skills improve an agent's results: nobody has measured that. The tests prove the files are well formed and consistent. See [What the tests do not cover](README.md#what-the-tests-do-not-cover).
