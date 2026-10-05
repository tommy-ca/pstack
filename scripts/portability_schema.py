"""Typed validation and domain model for pstack portability.

Implements the domain rules defined in openspec/specs/pstack-portability/spec.md
and issues #50 and #76. Pure Python with zero external dependencies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

SUPPORT_STATES = ("candidate", "mapped", "packaged", "verified", "supported")
IMPLEMENTATION_STATUSES = ("native", "shim", "version-gated", "gap")
ENFORCEMENT_LEVELS = ("hard", "soft", "advisory")
VERIFICATION_STATUSES = ("verified", "static-only", "unverified", "stale")
ADAPTATION_MODES = ("preserve", "adapt", "exclude", "gap")
HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "claude", "custom")

REQUIRED_CAPABILITIES = (
    "agent.spawn",
    "agent.join",
    "workspace.isolated",
    "workspace.readonly",
    "human.ask",
    "plan.update",
    "verify",
)

FORBIDDEN_ORCHESTRATION_FIELDS = (
    "spawn_topology",
    "fan_out_policy",
    "scheduler_behavior",
    "verifier_logic",
    "session_database",
)


class ValidationError(ValueError):
    pass


@dataclass
class Capability:
    id: str
    required_postconditions: List[str]
    description: Optional[str] = None

    def validate(self) -> None:
        if not self.id or "." not in self.id:
            raise ValidationError(f"Invalid capability id: {self.id!r}")
        if not self.required_postconditions:
            raise ValidationError(f"Capability {self.id} must declare at least one postcondition")


@dataclass
class Evidence:
    claim: str
    kind: Literal["static", "runtime", "external"]
    artifact: str
    command: Optional[str] = None
    verdict: Optional[Literal["PASS", "FAIL", "BLOCKED"]] = None
    timestamp: Optional[str] = None

    def validate(self) -> None:
        if not self.claim:
            raise ValidationError("Evidence claim cannot be empty")
        if self.kind not in ("static", "runtime", "external"):
            raise ValidationError(f"Invalid evidence kind: {self.kind!r}")
        if not self.artifact:
            raise ValidationError("Evidence artifact pointer cannot be empty")


@dataclass
class Binding:
    host: str
    capability: str
    implementation_status: str
    enforcement: str
    verification_status: str
    primitive: Optional[str] = None
    evidence_ref: Optional[str] = None
    notes: Optional[str] = None

    def validate(self) -> None:
        if self.host not in HOSTS:
            raise ValidationError(f"Unknown host: {self.host!r}")
        if self.implementation_status not in IMPLEMENTATION_STATUSES:
            raise ValidationError(f"Invalid implementation status: {self.implementation_status!r}")
        if self.enforcement not in ENFORCEMENT_LEVELS:
            raise ValidationError(f"Invalid enforcement level: {self.enforcement!r}")
        if self.verification_status not in VERIFICATION_STATUSES:
            raise ValidationError(f"Invalid verification status: {self.verification_status!r}")

        # Domain Rule: Prompt-only read-only posture cannot validate as hard enforcement
        if self.enforcement == "hard" and self.primitive:
            lowered = self.primitive.lower()
            if any(term in lowered for term in ("prompt", "convention", "advisory", "instruction", "soft")):
                raise ValidationError(
                    f"Prompt-only posture ({self.primitive}) cannot be validated as hard enforcement for {self.capability}"
                )

        # Domain Rule: Runtime claims cannot validate as verified without evidence reference
        if self.verification_status == "verified" and not self.evidence_ref:
            raise ValidationError(
                f"Binding for {self.capability} on {self.host} claimed verified without evidence_ref"
            )


@dataclass
class Adaptation:
    canonical_artifact: str
    mode: str
    reason: Optional[str] = None
    local_path: Optional[str] = None

    def validate(self) -> None:
        if self.mode not in ADAPTATION_MODES:
            raise ValidationError(f"Invalid adaptation mode: {self.mode!r}")
        if self.mode in ("exclude", "gap") and not self.reason:
            raise ValidationError(
                f"Adaptation {self.canonical_artifact} in mode {self.mode} requires an explicit reason"
            )


@dataclass
class PackageDescriptor:
    id: str
    name: str
    version: str
    upstream_pin: str
    host_targets: List[str]
    skills_root: str
    lifecycle: Dict[str, str]
    description: Optional[str] = None
    roles: List[Dict[str, str]] = field(default_factory=list)
    entrypoints: Dict[str, str] = field(default_factory=dict)
    namespace_policy: str = "prefixed"
    exclusions: List[str] = field(default_factory=list)
    raw_dict: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id:
            raise ValidationError("Package id cannot be empty")
        if len(self.upstream_pin) != 40:
            raise ValidationError(f"Invalid 40-hex upstream pin: {self.upstream_pin!r}")
        for host in self.host_targets:
            if host not in HOSTS:
                raise ValidationError(f"Unknown host target: {host!r}")
        for required_cycle in ("install", "verify", "uninstall"):
            if required_cycle not in self.lifecycle:
                raise ValidationError(f"Package descriptor missing lifecycle action: {required_cycle}")

        # Domain Rule: Package descriptor MUST NOT contain runtime orchestration fields
        for field_name in FORBIDDEN_ORCHESTRATION_FIELDS:
            if field_name in self.raw_dict:
                raise ValidationError(
                    f"Package descriptor must not encode runtime orchestration semantics: {field_name}"
                )


DEFAULT_SKILLS_DIRS = {
    "grok": ".grok/skills",
    "codex": ".codex/skills",
    "omp": ".omp/skills",
    "opencode": ".opencode/skills",
    "antigravity": ".agents/skills",
}

DEFAULT_PLUGIN_MANIFESTS = {
    "grok": ".grok-plugin/plugin.json",
    "codex": ".codex-plugin/plugin.json",
    "omp": ".omp-plugin/plugin.json",
    "opencode": ".opencode-plugin/package.json",
    "antigravity": ".antigravity-plugin/plugin.json",
}


@dataclass
class HarnessProfile:
    host: str
    support_state: str
    bindings: List[Binding]
    skills_dir: Optional[str] = None
    plugins_dir: Optional[str] = None
    plugin_manifest: Optional[str] = None
    package_descriptor: Optional[PackageDescriptor] = None
    evidence_ledger: List[Evidence] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.skills_dir is None and self.host in DEFAULT_SKILLS_DIRS:
            self.skills_dir = DEFAULT_SKILLS_DIRS[self.host]
        if self.plugin_manifest is None and self.host in DEFAULT_PLUGIN_MANIFESTS:
            self.plugin_manifest = DEFAULT_PLUGIN_MANIFESTS[self.host]

    def validate(self) -> None:
        if self.host not in HOSTS:
            raise ValidationError(f"Unknown host: {self.host!r}")
        if self.support_state not in SUPPORT_STATES:
            raise ValidationError(f"Invalid support state: {self.support_state!r}")
        if not self.skills_dir:
            raise ValidationError(f"Harness profile for {self.host} must declare a non-empty skills_dir")
        if not self.plugin_manifest:
            raise ValidationError(f"Harness profile for {self.host} must declare a plugin_manifest")


        for b in self.bindings:
            b.validate()
        for e in self.evidence_ledger:
            e.validate()
        if self.package_descriptor:
            self.package_descriptor.validate()

        # Domain Rule: Supported state requires all required capabilities to be verified with runtime evidence
        if self.support_state == "supported":
            bound_caps = {b.capability: b for b in self.bindings}
            for req in REQUIRED_CAPABILITIES:
                if req not in bound_caps:
                    raise ValidationError(f"Supported harness {self.host} missing required capability {req}")
                binding = bound_caps[req]
                if binding.verification_status != "verified":
                    raise ValidationError(
                        f"Supported harness {self.host} has unverified required capability {req}: {binding.verification_status}"
                    )
                if binding.implementation_status == "gap":
                    raise ValidationError(f"Supported harness {self.host} cannot have gap on required capability {req}")
