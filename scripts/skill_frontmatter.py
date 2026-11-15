"""Read and validate Agent Skills metadata and multi-host repository inventory."""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

SKILL_ROOTS: tuple[str, ...] = (
    "skills",
    ".agents/skills",
    ".codex/skills",
    ".factory/skills",
    ".grok/skills",
    ".omp/skills",
    ".opencode/skills",
    ".pi/skills",
    "automations/benny-grok/skills",
    "automations/benny/skills",
)

STANDARD_SPEC_FIELDS: frozenset[str] = frozenset({
    "name",
    "description",
    "compatibility",
    "license",
    "allowed-tools",
    "metadata",
})

PSTACK_EXTENSION_FIELDS: frozenset[str] = frozenset({
    "disable-model-invocation",
    "paths",
    "color",
    "icon",
    "reminder",
})

FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "mode",
})

ALL_RECOGNIZED_FIELDS: frozenset[str] = STANDARD_SPEC_FIELDS | PSTACK_EXTENSION_FIELDS


@dataclass(frozen=True)
class SkillRecord:
    name: str
    root_rel: str
    directory: pathlib.Path
    skill_file: pathlib.Path
    frontmatter: dict[str, Any]
    body: str


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
    if len(name) > 64:
        raise ValueError("frontmatter name must be at most 64 characters")
    return name


def validate_skill_description(description: str | None) -> str:
    """Enforce the Agent Skills required description length and nonblank value."""
    if not isinstance(description, str) or not description.strip():
        raise ValueError("frontmatter requires a nonempty description")
    if len(description) > 1024:
        raise ValueError("frontmatter description must be at most 1024 characters")
    return description


def _parse_frontmatter_dict(header: str | list[str]) -> dict[str, Any]:
    lines = header if isinstance(header, list) else header.splitlines(keepends=True)
    clean_lines: list[str] = []
    in_block = False
    for line in lines:
        stripped = line.rstrip("\r\n")
        if stripped == "---":
            if not in_block:
                in_block = True
                continue
            break
        if in_block:
            clean_lines.append(stripped)

    data: dict[str, Any] = {}
    idx = 0
    while idx < len(clean_lines):
        line = clean_lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue
        if ":" not in line:
            raise ValueError(f"invalid YAML in frontmatter: {line!r}")

        key_part, val_part = line.split(":", 1)
        key = key_part.strip()
        if key.startswith('"'):
            try:
                key = json.loads(key)
            except Exception as exc:
                raise ValueError(f"invalid YAML in frontmatter key: {exc}") from exc
        elif key.startswith("'"):
            key = key[1:-1].replace("''", "'")

        if key in data:
            raise ValueError(f"duplicate frontmatter '{key}'")

        val_stripped = val_part.strip()
        if "#" in val_stripped and not (val_stripped.startswith('"') or val_stripped.startswith("'")):
            val_stripped = val_stripped.split("#", 1)[0].strip()

        if not val_stripped:
            has_indented_child = False
            for peek_idx in range(idx + 1, len(clean_lines)):
                peek_line = clean_lines[peek_idx]
                if not peek_line.strip() or peek_line.strip().startswith("#"):
                    continue
                if peek_line.startswith(" ") or peek_line.startswith("\t"):
                    has_indented_child = True
                break

            if not has_indented_child:
                data[key] = ""
                idx += 1
                continue

            nested: dict[str, Any] = {}
            idx += 1
            while idx < len(clean_lines):
                next_line = clean_lines[idx]
                if not next_line.strip() or next_line.strip().startswith("#"):
                    idx += 1
                    continue
                if not next_line.startswith(" ") and not next_line.startswith("\t"):
                    break
                sub_stripped = next_line.strip()
                if ":" not in sub_stripped:
                    raise ValueError(f"invalid YAML in frontmatter: {sub_stripped!r}")
                sub_k, sub_v = sub_stripped.split(":", 1)
                sub_k = sub_k.strip().strip("\"'")
                sub_val_str = sub_v.strip()
                if "#" in sub_val_str and not (sub_val_str.startswith('"') or sub_val_str.startswith("'")):
                    sub_val_str = sub_val_str.split("#", 1)[0].strip()

                if sub_val_str.startswith('"'):
                    try:
                        v, end = json.JSONDecoder().raw_decode(sub_val_str)
                        sub_parsed: Any = v
                    except Exception as exc:
                        raise ValueError(f"invalid YAML in frontmatter: {exc}") from exc
                elif sub_val_str.startswith("'"):
                    sub_parsed = sub_val_str[1:-1].replace("''", "'")
                elif sub_val_str.lower() == "true":
                    sub_parsed = True
                elif sub_val_str.lower() == "false":
                    sub_parsed = False
                elif sub_val_str.isdigit():
                    sub_parsed = int(sub_val_str)
                else:
                    sub_parsed = sub_val_str.strip("\"'")
                nested[sub_k] = sub_parsed
                idx += 1
            data[key] = nested
            continue

        if val_stripped.startswith('"'):
            try:
                v, end = json.JSONDecoder().raw_decode(val_stripped)
                rest = val_stripped[end:].strip()
                if rest and not rest.startswith("#"):
                    raise ValueError("invalid YAML in frontmatter: trailing content after quote")
                val: Any = v
            except Exception as exc:
                raise ValueError(f"invalid YAML in frontmatter: {exc}") from exc
        elif val_stripped.startswith("'"):
            match = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", val_stripped)
            if match is None:
                raise ValueError("invalid YAML in frontmatter: unclosed single quote")
            val = match.group(1).replace("''", "'")
        elif val_stripped.startswith("{") and val_stripped.endswith("}"):
            inner = val_stripped[1:-1].strip()
            mapping: dict[str, Any] = {}
            if inner:
                for part in inner.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    if ":" not in part:
                        raise ValueError(f"invalid YAML in frontmatter: {part!r}")
                    mk, mv = part.split(":", 1)
                    mk = mk.strip().strip("\"'")
                    mv = mv.strip().strip("\"'")
                    if mv.lower() == "true":
                        mapping[mk] = True
                    elif mv.lower() == "false":
                        mapping[mk] = False
                    else:
                        mapping[mk] = mv
            val = mapping
        elif val_stripped.lower() == "true":
            val = True
        elif val_stripped.lower() == "false":
            val = False
        elif val_stripped.isdigit():
            val = int(val_stripped)
        elif val_stripped.startswith("[") and val_stripped.endswith("]"):
            inner = val_stripped[1:-1].strip()
            val = [x.strip().strip("\"'") for x in inner.split(",") if x.strip()]
        else:
            val = val_stripped

        data[key] = val
        idx += 1

    return data


def validate_skill_frontmatter(
    header: str | list[str],
    expected_dir: str | None = None,
    *,
    strict_spec: bool = False,
) -> dict[str, Any]:
    """Validate skill YAML frontmatter against specification contracts."""
    parsed = _parse_frontmatter_dict(header)

    for forbidden in FORBIDDEN_FIELDS:
        if forbidden in parsed:
            raise ValueError("retains Cursor-only frontmatter 'mode'")

    name = parsed.get("name")
    validate_skill_name(name, expected_dir)

    description = parsed.get("description")
    validate_skill_description(description)

    if strict_spec:
        unexpected = set(parsed.keys()) - STANDARD_SPEC_FIELDS
        if unexpected:
            fields_str = ", ".join(sorted(unexpected))
            raise ValueError(
                f"unexpected fields in frontmatter: {fields_str}. "
                "Only allowed-tools, compatibility, description, license, metadata, name are allowed."
            )
    else:
        unexpected = set(parsed.keys()) - ALL_RECOGNIZED_FIELDS
        if unexpected:
            fields_str = ", ".join(sorted(unexpected))
            raise ValueError(f"unexpected frontmatter fields: {fields_str}")

    if "compatibility" in parsed and not isinstance(parsed["compatibility"], str):
        raise ValueError("frontmatter compatibility must be a string")
    if "license" in parsed and not isinstance(parsed["license"], str):
        raise ValueError("frontmatter license must be a string")
    if "allowed-tools" in parsed:
        allowed = parsed["allowed-tools"]
        if not (isinstance(allowed, str) or (isinstance(allowed, list) and all(isinstance(x, str) for x in allowed))):
            raise ValueError("frontmatter allowed-tools must be a string or list of strings")
    if "metadata" in parsed:
        metadata = parsed["metadata"]
        if not isinstance(metadata, dict) or not all(isinstance(k, str) for k in metadata.keys()):
            raise ValueError("frontmatter metadata must be a mapping of string keys")
    if "disable-model-invocation" in parsed and not isinstance(parsed["disable-model-invocation"], bool):
        raise ValueError("frontmatter disable-model-invocation must be a boolean")
    if "paths" in parsed:
        paths = parsed["paths"]
        if not (isinstance(paths, str) or (isinstance(paths, list) and all(isinstance(x, str) for x in paths))):
            raise ValueError("frontmatter paths must be a string or list of strings")
    if "color" in parsed and not isinstance(parsed["color"], str):
        raise ValueError("frontmatter color must be a string")
    if "icon" in parsed and not isinstance(parsed["icon"], str):
        raise ValueError("frontmatter icon must be a string")
    if "reminder" in parsed and not isinstance(parsed["reminder"], str):
        raise ValueError("frontmatter reminder must be a string")

    return parsed


def dump_frontmatter_yaml(frontmatter: dict[str, Any]) -> str:
    """Format frontmatter mapping into valid YAML frontmatter block."""
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_k, sub_v in value.items():
                lines.append(f'  {sub_k}: "{sub_v}"')
        elif isinstance(value, list):
            items_str = ", ".join(f'"{x}"' for x in value)
            lines.append(f"{key}: [{items_str}]")
        elif isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        elif isinstance(value, str):
            if "\n" in value or ":" in value or "#" in value or value.startswith(("{", "[")):
                lines.append(f"{key}: {json.dumps(value)}")
            else:
                lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---\n")
    return "\n".join(lines)


def project_spec_frontmatter(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """Project native PStack frontmatter into strict Agent Skills reference format."""
    projected: dict[str, Any] = {}
    for key in ("name", "description", "compatibility", "license", "allowed-tools"):
        if key in frontmatter:
            projected[key] = frontmatter[key]

    meta: dict[str, str] = {}
    if "metadata" in frontmatter and isinstance(frontmatter["metadata"], dict):
        for k, v in frontmatter["metadata"].items():
            meta[str(k)] = str(v)

    for ext_key in PSTACK_EXTENSION_FIELDS:
        if ext_key in frontmatter:
            val = frontmatter[ext_key]
            meta[ext_key] = str(val).lower() if isinstance(val, bool) else str(val)

    if meta:
        projected["metadata"] = meta

    return projected


def discover_skills_inventory(root: pathlib.Path | None = None) -> list[SkillRecord]:
    """Discover and validate all Agent Skills across canonical and host-specific roots."""
    active_root = root if root is not None else pathlib.Path(__file__).resolve().parents[1]
    records: list[SkillRecord] = []
    seen_by_root: dict[str, set[str]] = {}

    for rel_root in SKILL_ROOTS:
        skill_root = active_root / rel_root
        if not skill_root.exists() or not skill_root.is_dir():
            continue
        seen_by_root[rel_root] = set()
        for child in sorted(skill_root.iterdir()):
            if not child.is_dir():
                continue
            skill_file = child / "SKILL.md"
            if not skill_file.is_file():
                raise ValueError(f"skill directory {child.name} under {rel_root} missing SKILL.md")

            raw_text = skill_file.read_text(encoding="utf-8")
            header_lines, body = split_frontmatter(raw_text)
            frontmatter = validate_skill_frontmatter(header_lines, expected_dir=child.name)
            name = frontmatter["name"]
            if name in seen_by_root[rel_root]:
                raise ValueError(f"duplicate skill {name!r} under {rel_root}")
            seen_by_root[rel_root].add(name)

            records.append(
                SkillRecord(
                    name=name,
                    root_rel=rel_root,
                    directory=child,
                    skill_file=skill_file,
                    frontmatter=frontmatter,
                    body=body,
                )
            )

    return records
