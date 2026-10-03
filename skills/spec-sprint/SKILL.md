---
name: spec-sprint
description: Turns a vague software idea into a short, implementation-ready specification (SPEC.md) and an ordered task plan (PLAN.md) before any code is written. Use when the user describes a new project, feature, or tool in loose terms, asks to plan, scope, spec out, or write requirements, or gives a task too ambiguous to start safely. Not for small, well-defined fixes. Pairs with the proof-build skill, which implements the plan one task at a time.
license: MIT
metadata:
  author: spec-and-proof contributors
  version: "0.1.0"
---

# SpecSprint

The output of this skill is a one-to-two page spec and a task list that a coding agent can execute without guessing. This skill plans. It does not write application code.

## When to use it

Use it when the request is loose ("I want an app that tracks my spending"), when requirements conflict or are missing, or when the user asks for a plan before building. Skip it for small, clear changes such as a typo, a one-line fix, or a question about existing code. Just do those.

## 1. Understand the goal

- If a repository exists, read its README, package manifest, and top-level layout first. The spec should fit the stack and conventions already there.
- Write down three things in your own words: the goal (what is true when this is done), the intended users, and the problem they have today.
- Say that back to the user in a sentence or two. A wrong restatement costs little to fix now and a lot later.

## 2. Find the ambiguity

Scan for what is unknown or unstated: who uses it, what it must do on day one, where data lives, platform and language, scale, deadlines, integrations, what success looks like, and what the user does not want. Sort each unknown:

- Blocking: different answers lead to different designs or wasted work.
- Non-blocking: a sensible default exists, so assume it.

Also capture the constraints the user already gave (stack, time, offline only) and anything they ruled out.

## 3. Ask only what blocks you

- Ask at most three questions, and only blocking ones. Attach a default to each ("I'll assume a command-line tool that stores JSON locally unless you say otherwise") so a one-word answer is enough.
- Never ask what the repo or the user's message already answers.
- If the user says to proceed, or nobody can answer (an autonomous run), do not wait. Turn every open question into a labeled assumption in the spec and keep going.

## 4. Write the specification

Use [the spec template](assets/SPEC.template.md). Sections, in order: Problem, Target users, Proposed solution, Core features, Non-goals, Technical constraints, Assumptions, Acceptance criteria, Risks and open questions.

- Keep it to one or two pages. A section with nothing real to say gets one line, not filler.
- Core features cover the MVP only, and each one maps to at least one acceptance criterion.
- Non-goals name things a reasonable person might expect that you are leaving out. Any non-trivial project has at least one.
- Acceptance criteria are numbered (AC1, AC2, ...) and observable: a command with its expected output, or a given/when/then. Reject vague words such as "fast", "intuitive", or "works well" unless you attach a number or a concrete check.
- Risks say what could go wrong and what you would do about it. Open questions are things only the user can answer.
- Mark guesses as assumptions. Do not present them as facts.

## 5. Plan the tasks

Use [the plan template](assets/PLAN.template.md). Each task has:

- an ID and title (T1, T2, ...)
- Size: small enough to finish and verify in one sitting
- Depends on: earlier task IDs, or none
- Done when: an observable condition, not "implemented"
- Verify with: the exact command or manual check that shows it is done. If the project has no test setup yet, creating one is part of T1.
- Covers: the acceptance criteria this task satisfies

Write tasks as checkboxes (`- [ ] T1: title`) so that proof-build can find the next unchecked one. Order them so the first task produces something that runs end to end, even if crude, and every later task leaves the project in a working state. Tests come with the code they test. Put the riskiest unknown early.

## 6. Cut to the smallest useful MVP

- Draw a line in PLAN.md. Tasks above it are the MVP. Everything else goes under "Later".
- For each feature ask: if this were removed, could a user still get the core value? If yes, move it to Later.
- When a new idea shows up mid-conversation, from you or the user, it goes to Later unless an acceptance criterion needs it. Say that you are doing so.
- State the MVP in one sentence: "A [user] can [do something] and see [result]."

## 7. Write the files

- Default to SPEC.md and PLAN.md in the project root, or in docs/ if the repo already keeps documents there.
- Never overwrite an existing file without permission. If SPEC.md or PLAN.md exists, ask whether to replace it, merge into it, or write beside it. If you cannot ask, write SPEC.proposed.md or PLAN.proposed.md and tell the user.
- If the user only wants to talk an idea through, or the job is tiny, give the spec in the reply and create no files.
- Do not commit the files. That is the user's call.

## 8. Hand off

Finish with a short message: the one-sentence MVP, the assumptions most worth checking, the open questions only the user can answer, and the next step ("start with T1 using proof-build"). Do not begin implementing unless the user asks.

Before you hand off, check the plan against these questions:

- Could another engineer start T1 without asking you anything?
- Does every task say how to know it is done?
- Does every acceptance criterion map to a task, and every task to a criterion?
- Are the non-goals written down?
