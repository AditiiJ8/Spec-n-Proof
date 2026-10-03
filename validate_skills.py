#!/usr/bin/env python3
"""Validate Agent Skills in this repository. Standard library only.

Usage:
    python3 tests/validate_skills.py              # validates ./skills
    python3 tests/validate_skills.py PATH         # a skills directory, or one skill directory

Exit status is 0 when every skill is valid and 1 otherwise.

What is checked comes from the public specification at
https://agentskills.io/specification (fetched while building this project):

  - SKILL.md exists and starts with YAML frontmatter
  - name: required, 1-64 chars, lowercase letters/digits/hyphens, no leading or
    trailing hyphen, no "--", and equal to the parent directory name
  - description: required, 1-1024 chars, non-empty
  - license, compatibility (1-500 chars), metadata (string keys to string
    values), allowed-tools: optional, type-checked when present
  - no frontmatter fields outside that list
  - the body stays under 500 lines (the spec recommends this; reported as a warning)
  - relative file references resolve and stay inside the skill directory

On top of the spec, this project also checks that the two bundled skills contain
their expected workflow stages and key phrases (see WORKFLOWS below).

Known limits:
  - The frontmatter parser reads only the YAML subset the spec uses: top-level
    "key: value" pairs and one nested mapping (metadata). Block scalars (| and >),
    lists, and anchors are rejected with a clear message instead of being guessed at.
  - Name characters are checked with str.isalnum() and str.lower(). The official
    skills-ref library may treat unusual Unicode letters differently.
  - The reference library (skills-ref) is the authority. This file is a lightweight
    stand-in that needs no dependencies.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_BODY_LINES = 500

# Workflow stages are matched, in order, as lowercase substrings of "## " headings.
# Phrases are case-sensitive substrings that must appear in the body.
WORKFLOWS = {
    "spec-sprint": {
        "stages": [
            "understand",
            "ambiguity",
            "ask",
            "specification",
            "plan",
            "mvp",
            "write the files",
            "hand off",
        ],
        "phrases": [
            "SPEC.md",
            "PLAN.md",
            "overwrite",
            "Non-goals",
            "Acceptance criteria",
            "assumption",
            "Done when",
            "Verify with",
        ],
    },
    "proof-build": {
        "stages": [
            "inspect",
            "one task",
            "tests first",
            "implement",
            "run the checks",
            "fix failures",
            "review the diff",
            "report",
        ],
        "phrases": [
            "PASS",
            "FAIL",
            "NOT RUN",
            "BLOCKED",
            "approval",
            "commit",
            "push",
            "PLAN.md",
            "Done when",
            "Verify with",
        ],
    },
}

LINK_RE = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
BARE_PATH_RE = re.compile(r"(?<![\w/.\-])((?:assets|references|scripts)/\w[\w./\-]*)")
NON_STRING_SCALAR_RE = re.compile(
    r"^(true|false|yes|no|on|off|null|~|[-+]?(\d[\d_]*)(\.\d*)?([eE][-+]?\d+)?|0x[0-9a-fA-F]+)$",
    re.IGNORECASE,
)


class FrontmatterError(ValueError):
    """The frontmatter is missing, malformed, or uses YAML this validator does not read."""


@dataclass
class Report:
    skill: str
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# ---------------------------------------------------------------- frontmatter

def split_frontmatter(text: str):
    """Return (frontmatter_block, body). Raise FrontmatterError if not well formed."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("file must start with a line containing only '---'")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    raise FrontmatterError("frontmatter is never closed with a line containing only '---'")


def _scalar(value: str, where: str) -> str:
    """Read one YAML scalar and always return a string."""
    if value[0] in "|>[{&*!%@`":
        raise FrontmatterError(
            f"{where}: unsupported YAML ({value[0]!r}). Use a plain or quoted single-line string."
        )
    if value[0] in "\"'":
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise FrontmatterError(f"{where}: quoted string is not closed")
        inner = value[1:-1]
        if quote == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner
    if ": " in value or " #" in value or value.endswith(":"):
        raise FrontmatterError(
            f"{where}: an unquoted value contains ': ' or ' #', which YAML parsers reject "
            "or misread. Reword it or wrap the whole value in quotes."
        )
    if NON_STRING_SCALAR_RE.match(value):
        raise FrontmatterError(
            f"{where}: {value!r} would be read as a number, boolean, or null. "
            "Wrap it in quotes so it is a string."
        )
    return value


def parse_frontmatter(block: str) -> dict:
    """Parse the small YAML subset used by SKILL.md frontmatter."""
    data: dict = {}
    current = None  # key of the mapping being filled, if any
    for number, raw in enumerate(block.splitlines(), start=2):  # line 1 is the opening '---'
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise FrontmatterError(f"line {number}: tabs are not allowed for indentation")
        indent = len(raw) - len(raw.lstrip(" "))
        key, sep, value = raw.strip().partition(":")
        key, value = key.strip(), value.strip()
        if not sep or not key or " " in key:
            raise FrontmatterError(f"line {number}: expected 'key: value', got {raw.strip()!r}")
        if indent == 0:
            if key in data:
                raise FrontmatterError(f"line {number}: duplicate key {key!r}")
            if value == "":
                data[key] = {}
                current = key
            else:
                data[key] = _scalar(value, f"line {number} ({key})")
                current = None
        else:
            if current is None:
                raise FrontmatterError(f"line {number}: unexpected indentation")
            if value == "":
                raise FrontmatterError(f"line {number}: nested values must be single-line strings")
            if key in data[current]:
                raise FrontmatterError(f"line {number}: duplicate key {key!r} under {current!r}")
            data[current][key] = _scalar(value, f"line {number} ({current}.{key})")
    return data


# ------------------------------------------------------------------- checkers

def check_name(name: str, directory_name: str) -> list:
    errors = []
    if not 1 <= len(name) <= MAX_NAME:
        errors.append(f"name must be 1-{MAX_NAME} characters (got {len(name)})")
    if name.startswith("-") or name.endswith("-"):
        errors.append("name must not start or end with a hyphen")
    if "--" in name:
        errors.append("name must not contain consecutive hyphens")
    bad = sorted({c for c in name if not (c == "-" or (c.isalnum() and c == c.lower()))})
    if bad:
        errors.append(
            "name may only contain lowercase letters, digits and hyphens "
            f"(found {', '.join(repr(c) for c in bad)})"
        )
    if name != directory_name:
        errors.append(f"name {name!r} must match its directory name {directory_name!r}")
    return errors


def _check_fields(meta: dict, skill_dir: Path, report: Report) -> None:
    for key in sorted(set(meta) - ALLOWED_FIELDS):
        report.errors.append(f"unknown frontmatter field {key!r}")

    name = meta.get("name")
    if not isinstance(name, str) or not name:
        report.errors.append("name is required and must be a non-empty string")
    else:
        report.errors.extend(check_name(name, skill_dir.name))

    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        report.errors.append("description is required and must be a non-empty string")
    elif len(description) > MAX_DESCRIPTION:
        report.errors.append(f"description is {len(description)} characters (max {MAX_DESCRIPTION})")

    for key in ("license", "allowed-tools"):
        if key in meta and (not isinstance(meta[key], str) or not meta[key].strip()):
            report.errors.append(f"{key} must be a non-empty string when present")

    if "compatibility" in meta:
        value = meta["compatibility"]
        if not isinstance(value, str) or not 1 <= len(value) <= MAX_COMPATIBILITY:
            report.errors.append(f"compatibility must be a string of 1-{MAX_COMPATIBILITY} characters")

    if "metadata" in meta:
        value = meta["metadata"]
        if not isinstance(value, dict):
            report.errors.append("metadata must be a mapping of string keys to string values")
        elif not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
            report.errors.append("metadata keys and values must all be strings")


def _in_code_fence_stripped(body: str) -> str:
    """Return the body with fenced code blocks removed."""
    kept, inside = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            kept.append(line)
    return "\n".join(kept)


def headings(body: str, prefix: str = "## ") -> list:
    return [
        line[len(prefix):].strip()
        for line in _in_code_fence_stripped(body).splitlines()
        if line.startswith(prefix)
    ]


def missing_stages(found_headings: list, keywords: list) -> list:
    """Return keywords not found in order among the headings."""
    missing, position = [], 0
    lowered = [h.lower() for h in found_headings]
    for keyword in keywords:
        for index in range(position, len(lowered)):
            if keyword in lowered[index]:
                position = index + 1
                break
        else:
            missing.append(keyword)
    return missing


def referenced_paths(text: str, bare_paths: bool = True) -> list:
    """Relative file references: markdown links, plus (optionally) bare assets/, references/,
    scripts/ paths. Bare paths are a SKILL.md convention, relative to the skill folder, so
    they are not meaningful in a README."""
    found = []
    for target in LINK_RE.findall(text):
        target = target.split("#", 1)[0]
        if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", target):
            continue  # anchor-only, or a URL/mailto
        found.append(target)
    if bare_paths:
        for target in BARE_PATH_RE.findall(text):
            found.append(target.rstrip(".,;:)"))
    seen, ordered = set(), []
    for target in found:
        if target not in seen:
            seen.add(target)
            ordered.append(target)
    return ordered


def check_links(markdown_file: Path, boundary: Path = None, bare_paths: bool = False) -> list:
    """Return error strings for relative references in a markdown file that do not resolve.

    Markdown links are always checked. Set bare_paths=True (as done for SKILL.md) to also
    check plain-text assets/, references/ and scripts/ paths. If boundary is given,
    references that resolve outside that directory are errors too.
    """
    errors = []
    base = markdown_file.parent
    text = markdown_file.read_text(encoding="utf-8-sig")
    for target in referenced_paths(text, bare_paths=bare_paths):
        resolved = (base / target).resolve()
        if boundary is not None and boundary.resolve() not in (resolved, *resolved.parents):
            errors.append(f"{markdown_file.name}: reference {target!r} points outside {boundary.name}/")
        elif not resolved.exists():
            errors.append(f"{markdown_file.name}: reference {target!r} does not exist")
    return errors


def validate_skill(skill_dir) -> Report:
    skill_dir = Path(skill_dir)
    report = Report(skill=skill_dir.name)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        report.errors.append("SKILL.md is missing (the file name is case-sensitive)")
        return report
    try:
        text = skill_md.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        report.errors.append(f"cannot read SKILL.md as UTF-8: {exc}")
        return report

    try:
        block, body = split_frontmatter(text)
        meta = parse_frontmatter(block)
    except FrontmatterError as exc:
        report.errors.append(f"frontmatter: {exc}")
        return report

    _check_fields(meta, skill_dir, report)

    body_lines = len(body.splitlines())
    if not body.strip():
        report.warnings.append("body is empty, so the skill gives the agent no instructions")
    if body_lines > MAX_BODY_LINES:
        report.warnings.append(
            f"body is {body_lines} lines; the spec recommends under {MAX_BODY_LINES}. "
            "Move detail into references/."
        )

    report.errors.extend(check_links(skill_md, boundary=skill_dir, bare_paths=True))

    workflow = WORKFLOWS.get(skill_dir.name)
    if workflow:
        for keyword in missing_stages(headings(body), workflow["stages"]):
            report.errors.append(f"workflow stage missing or out of order: no '## ' heading matching {keyword!r}")
        for phrase in workflow["phrases"]:
            if phrase not in body:
                report.errors.append(f"expected phrase not found in body: {phrase!r}")
    return report


def find_skill_dirs(path: Path) -> list:
    if (path / "SKILL.md").exists():
        return [path]
    return sorted(p for p in path.iterdir() if p.is_dir() and not p.name.startswith("."))


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]) if argv else Path(__file__).resolve().parent.parent / "skills"
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1
    skill_dirs = find_skill_dirs(root)
    if not skill_dirs:
        print(f"error: no skill directories found in {root}", file=sys.stderr)
        return 1

    failed = False
    for skill_dir in skill_dirs:
        report = validate_skill(skill_dir)
        status = "OK" if report.ok else "FAIL"
        print(f"[{status}] {report.skill}")
        for message in report.errors:
            print(f"    error: {message}")
        for message in report.warnings:
            print(f"    warning: {message}")
        failed = failed or not report.ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
