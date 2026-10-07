"""Read selected skill metadata without interpreting the document body."""

from __future__ import annotations

import json
import re

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ValueError("missing exact frontmatter opening '---'")
    for index, line in enumerate(lines[1:], 1):
        if line.rstrip("\r\n") == "---":
            return lines[:index + 1], "".join(lines[index + 1:])
    raise ValueError("missing frontmatter closing '---'")


def is_scalar_key(line: str, key: str) -> bool:
    match = re.match(r"^([a-zA-Z0-9_-]+|\"(?:[^\"\\]|\\.)*\"|'(?:[^']|'')*')\s*:", line)
    if match is None:
        return False
    raw = match.group(1)
    if raw.startswith('"'):
        try:
            raw = json.loads(raw)
        except ValueError as exc:
            raise ValueError("unsupported quoted frontmatter key") from exc
    elif raw.startswith("'"):
        raw = raw[1:-1].replace("''", "'")
    return raw == key


def read_scalar(header: list[str], key: str) -> str | None:
    matches = [index for index, line in enumerate(header[1:-1], 1) if is_scalar_key(line, key)]
    if len(matches) > 1:
        raise ValueError(f"duplicate frontmatter '{key}'")
    if not matches:
        return None
    index = matches[0]
    for line in header[index + 1:-1]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace():
            raise ValueError(f"multiline frontmatter '{key}' is not supported")
        break
    raw = header[index].split(":", 1)[1].strip()
    if raw.startswith('"'):
        try:
            value, end = json.JSONDecoder().raw_decode(raw)
        except ValueError as exc:
            raise ValueError(f"invalid quoted '{key}'") from exc
        rest = raw[end:].strip()
        if not isinstance(value, str) or (rest and not rest.startswith("#")):
            raise ValueError(f"invalid scalar '{key}'")
        return value
    if raw.startswith("'"):
        match = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", raw)
        if match is None:
            raise ValueError(f"invalid quoted '{key}'")
        return match.group(1).replace("''", "'")
    value = re.split(r"\s+#", raw, maxsplit=1)[0].strip()
    if not value or value.startswith(("#", "[", "{", "|", ">", "&", "*", "!")):
        raise ValueError(f"invalid scalar '{key}'")
    return value


def validate_skill_name(name: str | None, expected: str | None = None) -> str:
    if name is None or not SKILL_NAME_RE.fullmatch(name):
        raise ValueError(f"frontmatter name {name!r} is not kebab-case")
    if expected is not None and name != expected:
        raise ValueError(f"frontmatter name {name!r} does not match directory name {expected!r}")
    return name
