#!/usr/bin/env python3
"""Single source of truth for harness host identity (#446).

The portability core used to declare the host set in ten places: the closed
`HOSTS` tuple, three `SUPPORTED_HOSTS` copies, `TARGET_MAP`, `DRIVER_REGISTRY`,
the boundary scanner's name set and four JSON schema enums. Supporting a harness
therefore meant editing central domain models, and the `custom` placeholder could
not tell two unnamed harnesses apart. This module owns the identity set and the
rule a *declared* host id must satisfy; every surface imports it instead of
keeping its own copy.

Identity is not capability. A declared host may be described by a local adapter
profile, but it starts at `candidate` with unproved bindings, and a receipt for
it must name the exact `adapter_version` it was produced by. Native evidence is
what promotes a host, never the declaration. See #446 (built-in registry plus
validated namespaced external ids) and the parent epic #432.
"""

from __future__ import annotations

import re
from typing import Iterable, Tuple

# The six hosts pstack ships native drivers, projections and receipts for. Closed
# on purpose: a seventh entry is a deliberate act with native packaging, a driver
# and evidence behind it, not a config edit.
BUILTIN_HOSTS: Tuple[str, ...] = ("grok", "codex", "omp", "opencode", "antigravity", "droid")

# Names from before the registry that existing profiles, bindings and receipts
# still carry: `claude` is the fork-ledger alias, `custom` the pre-#446
# placeholder for an unnamed harness. They stay readable, but they are aliases a
# new harness may not reuse as an identity.
LEGACY_HOST_ALIASES: Tuple[str, ...] = ("claude", "custom")

# A host a receipt may name for an observation that is not a real harness.
OBSERVER_HOSTS: Tuple[str, ...] = ("mock",)

# Every identity a profile, binding or package descriptor may carry.
KNOWN_HOSTS: Tuple[str, ...] = BUILTIN_HOSTS + LEGACY_HOST_ALIASES

# The one bare harness name `scripts/scan-host-boundary.py` knows without this
# module (`HARNESS_NAMES = set(KNOWN_HOSTS) | set(OBSERVER_HOSTS) | {"pi"}`), so
# its namespace is spent too.
SCANNED_ONLY_HOST_NAMES: Tuple[str, ...] = ("pi",)

# Every name the flat namespace already spends, derived so a seventh built-in
# reserves itself. A namespace reusing one would shadow a harness with a declared
# identity, which is the collision the bare-name rule refuses one level down.
RESERVED_NAMESPACES: Tuple[str, ...] = KNOWN_HOSTS + OBSERVER_HOSTS + SCANNED_ONLY_HOST_NAMES

# A declared host MUST be namespaced: `<namespace>:<name>`, two lowercase labels.
# A bare new name would collide with the flat built-in namespace and reopen the
# central enum, so it is refused; `acme:copilot` and `beta:copilot` are two
# distinct identities that coexist. No dots, slashes, underscores or uppercase,
# so an id can never be read as a path or a host name to probe. Both clauses live
# in the string, because every carrier of this rule is compiled by Python `re` in
# this repo: the head refuses a reserved namespace, and `(?!\n)$` pins the end of
# the string, since Python's `$` also matches before a trailing newline and such
# an id lands inside `f"{host}-receipt.json"` (#446).
EXTERNAL_HOST_ID_PATTERN = (
    r"^(?!(?:" + "|".join(RESERVED_NAMESPACES) + r"):)"
    r"[a-z][a-z0-9-]{1,31}:[a-z][a-z0-9-]{1,47}(?!\n)$"
)
EXTERNAL_HOST_ID_RE = re.compile(EXTERNAL_HOST_ID_PATTERN)


class HostIdentityError(ValueError):
    """A host id outside every identity this module declares."""


def is_builtin(host_id: str) -> bool:
    """True for the six hosts pstack ships native support for."""
    return host_id in BUILTIN_HOSTS


def is_external(host_id: str) -> bool:
    """True for a declared, namespaced host id (`acme:copilot`).

    `fullmatch`, not `match`: the Python carrier keeps its own end-of-string
    guarantee instead of relying on the pattern's `(?!\n)$`, which exists because
    the schema this repo validates with shares the same semantics (#446).
    """
    return isinstance(host_id, str) and bool(EXTERNAL_HOST_ID_RE.fullmatch(host_id))


def is_declared_host(host_id: str) -> bool:
    """True for every non-built-in harness identity: a namespaced id or an alias.

    Neither ships a native driver, projection or receipt, so both walk the
    declared-host gates: the profile stays `candidate`, and its receipt must name
    the `adapter_version` it was produced by. A legacy alias is therefore gated
    exactly like a declared host - the name is historical spelling, not a
    capability, and keying those gates on `is_external` alone let `custom` and
    `claude` through them (#446). `mock` is not here: it names an observation,
    not a harness.
    """
    return is_external(host_id) or host_id in LEGACY_HOST_ALIASES


def is_valid_host_id(host_id: str) -> bool:
    """True for every identity a profile, binding or descriptor may carry."""
    return host_id in KNOWN_HOSTS or is_external(host_id)


def is_valid_receipt_host(host_id: str) -> bool:
    """True for every identity a receipt may carry, observers included."""
    return is_valid_host_id(host_id) or host_id in OBSERVER_HOSTS


def require_builtin_host_keys(host_keys: Iterable[str], surface: str) -> None:
    """Fail closed when a per-host routing table drifts from the built-in set.

    The tables themselves stay where they are - each row routes one host to its
    own driver class, plugin directory or projection generator - but their key
    set *is* the identity set, so it is checked against this module instead of
    being restated as another enum.
    """
    missing = sorted(set(BUILTIN_HOSTS) - set(host_keys))
    extra = sorted(set(host_keys) - set(BUILTIN_HOSTS))
    if missing or extra:
        raise HostIdentityError(
            f"{surface} must cover exactly the built-in hosts: missing={missing}, unexpected={extra}"
        )
