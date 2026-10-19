"""Typed validation and domain model for pstack portability.

Implements the domain rules defined in openspec/specs/pstack-portability/spec.md
and issues #50 and #76. Pure Python with zero external dependencies.
"""

from __future__ import annotations

import ast
import base64
import binascii
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from scripts.host_identity import (
    KNOWN_HOSTS,
    is_declared_host,
    is_valid_host_id,
    is_valid_receipt_host,
    require_builtin_host_keys,
)

SUPPORT_STATES = ("candidate", "mapped", "packaged", "verified", "supported")
IMPLEMENTATION_STATUSES = ("native", "shim", "version-gated", "gap")
ENFORCEMENT_LEVELS = ("hard", "soft", "advisory")
VERIFICATION_STATUSES = ("verified", "static-only", "unverified", "stale")
ADAPTATION_MODES = ("preserve", "adapt", "exclude", "gap")
# The closed pre-registry set, kept as a readable name for importers. Validation
# goes through `host_identity.is_valid_host_id`, so a declared namespaced host id
# is accepted without editing this tuple (#446).
HOSTS = KNOWN_HOSTS

CONFORMANCE_PLANES = ("canonical", "adapter", "package", "runtime")

# Dependency/cache artifacts that must never perturb skills_tree_hash. Ignored
# at hash time so extracted non-Git packages stay invariant too; no Git state.
SKILLS_HASH_IGNORED_DIRS = frozenset({"__pycache__", "node_modules"})
SKILLS_HASH_IGNORED_SUFFIXES = (".pyc", ".pyo")

MANDATORY_SUPPORT_FLOOR = (
    "agent.spawn",
    "agent.join",
    "workspace.shared",
    "workspace.isolated",
    "workspace.readonly",
    "human.ask",
    "plan.update",
    "verify",
    "evidence.capture",
)

CONDITIONAL_CAPABILITIES: Dict[str, str] = {
    "schedule": "orchestrate, overnight, autopilot-full",
    "monitor": "orchestrate, monitor-watcher, loop",
    "session.persist": "pause-safely",
    "session.resume": "session-pickup",
    "agent.message": "interactive multi-agent collaboration",
    "agent.cancel": "task cancellation and kill",
    "agent.resume": "subagent resume from checkpoint",
    "human.gate": "irreversible action confirmation",
}

PORTABLE_CAPABILITY_UNIVERSE = MANDATORY_SUPPORT_FLOOR + tuple(sorted(CONDITIONAL_CAPABILITIES.keys()))

# Terminal outcomes a capability may pin as its own settled proof, on top of the
# successful spawn/join settlement every capability can pin. A cancellation settles
# `agent.cancel` and proves nothing about any other capability (#381), so the extra
# outcome stays scoped to the capability that owns it.
SETTLEMENT_PROMOTIONS: Dict[str, tuple] = {
    "agent.cancel": ("cancelled",),
}

REQUIRED_CAPABILITIES = MANDATORY_SUPPORT_FLOOR

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
    surface_revisions: Optional[Dict[str, Any]] = None

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
    evidence_ref: Optional[str | Dict[str, str]] = None
    notes: Optional[str] = None

    @property
    def receipt_ref(self) -> Optional[str]:
        """Receipt this binding points at, whether pinned to a scenario or receipt-only."""
        if isinstance(self.evidence_ref, dict):
            return self.evidence_ref.get("receipt")
        return self.evidence_ref

    @property
    def scenario_id(self) -> Optional[str]:
        """Scenario this binding pins, or None for a receipt-only reference."""
        if isinstance(self.evidence_ref, dict):
            return self.evidence_ref.get("scenario")
        return None

    def validate(self) -> None:
        if not is_valid_host_id(self.host):
            raise ValidationError(f"Unknown host: {self.host!r}")
        if self.capability not in PORTABLE_CAPABILITY_UNIVERSE:
            raise ValidationError(f"Unknown capability: {self.capability!r}")
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

        if isinstance(self.evidence_ref, dict):
            if set(self.evidence_ref) != {"receipt", "scenario"} or not all(
                isinstance(value, str) and value for value in self.evidence_ref.values()
            ):
                raise ValidationError(
                    f"Binding for {self.capability} on {self.host} must pin a non-empty receipt and scenario"
                )

        # Domain Rule: Runtime claims cannot validate as verified without evidence reference
        if self.verification_status == "verified" and not self.receipt_ref:
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


REQUIRED_TOOL_MAPPINGS = (
    "file_read",
    "file_edit",
    "shell_run",
    "agent_spawn",
    "agent_join",
    "plan_update",
    "human_ask",
)

ALLOWED_TOOL_MAPPINGS = (
    "file_read",
    "file_edit",
    "file_write",
    "shell_run",
    "web_fetch",
    "web_search",
    "agent_spawn",
    "agent_fanout",
    "agent_join",
    "agent_message",
    "task_background",
    "tool_mcp",
    "plan_update",
    "human_ask",
)


@dataclass
class ToolMapping:
    file_read: str
    file_edit: str
    shell_run: str
    agent_spawn: str
    agent_join: str
    plan_update: str
    human_ask: str
    file_write: Optional[str] = None
    web_fetch: Optional[str] = None
    web_search: Optional[str] = None
    agent_fanout: Optional[str] = None
    agent_message: Optional[str] = None
    task_background: Optional[str] = None
    tool_mcp: Optional[str] = None

    def validate(self) -> None:
        required = (
            ("file_read", self.file_read),
            ("file_edit", self.file_edit),
            ("shell_run", self.shell_run),
            ("agent_spawn", self.agent_spawn),
            ("agent_join", self.agent_join),
            ("plan_update", self.plan_update),
            ("human_ask", self.human_ask),
        )
        for name, val in required:
            if not val or not isinstance(val, str) or not val.strip():
                raise ValidationError(f"ToolMapping missing or empty required field: {name}")


@dataclass
class SkillOrderItem:
    need: str
    primary_pstack: Optional[str] = None
    secondary_user: Optional[str] = None
    fallback_builtin: Optional[str] = None
    notes: Optional[str] = None

    def validate(self) -> None:
        if not self.need or not isinstance(self.need, str) or not self.need.strip():
            raise ValidationError("SkillOrderItem need cannot be empty")


@dataclass
class RuntimeConventions:
    max_subagent_depth: int
    supported_isolation_modes: List[str]
    default_model: str
    allowed_spawn_fields: List[str]
    forbidden_spawn_fields: List[str]
    wire_aliases: Dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not isinstance(self.max_subagent_depth, int) or self.max_subagent_depth < 1:
            raise ValidationError(f"Invalid max_subagent_depth: {self.max_subagent_depth}")
        if not self.supported_isolation_modes or not isinstance(self.supported_isolation_modes, list):
            raise ValidationError("supported_isolation_modes cannot be empty")
        if not self.default_model or not isinstance(self.default_model, str):
            raise ValidationError("default_model cannot be empty")
        if not isinstance(self.allowed_spawn_fields, list):
            raise ValidationError("allowed_spawn_fields must be a list")
        if not isinstance(self.forbidden_spawn_fields, list):
            raise ValidationError("forbidden_spawn_fields must be a list")


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
    host_adapters: Dict[str, Any] = field(default_factory=dict)
    roles: List[Dict[str, str]] = field(default_factory=list)
    commands: List[Dict[str, str]] = field(default_factory=list)
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
            if not is_valid_host_id(host):
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
    "droid": ".factory/skills",
}

DEFAULT_PLUGIN_MANIFESTS = {
    "grok": ".grok-plugin/plugin.json",
    "codex": ".codex-plugin/plugin.json",
    "omp": ".omp-plugin/package.json",
    "opencode": ".opencode-plugin/package.json",
    "antigravity": ".antigravity-plugin/plugin.json",
    "droid": ".factory-plugin/plugin.json",
}

# One row per built-in host, no more and no less: the key set is the identity set
# (#446), so a seventh host cannot be added to the census while these two tables
# silently miss it.
require_builtin_host_keys(DEFAULT_SKILLS_DIRS, "DEFAULT_SKILLS_DIRS")
require_builtin_host_keys(DEFAULT_PLUGIN_MANIFESTS, "DEFAULT_PLUGIN_MANIFESTS")


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
    tool_mappings: Optional[ToolMapping | Dict[str, Any]] = None
    skill_order: Optional[List[SkillOrderItem] | List[Dict[str, Any]]] = None
    runtime_conventions: Optional[RuntimeConventions | Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.skills_dir is None and self.host in DEFAULT_SKILLS_DIRS:
            self.skills_dir = DEFAULT_SKILLS_DIRS[self.host]
        if self.plugin_manifest is None and self.host in DEFAULT_PLUGIN_MANIFESTS:
            self.plugin_manifest = DEFAULT_PLUGIN_MANIFESTS[self.host]
        if isinstance(self.tool_mappings, dict):
            extra_keys = set(self.tool_mappings.keys()) - set(ALLOWED_TOOL_MAPPINGS)
            if extra_keys:
                raise ValidationError(f"Unknown fields in tool_mappings: {sorted(extra_keys)}")
            try:
                self.tool_mappings = ToolMapping(**self.tool_mappings)
            except TypeError as err:
                raise ValidationError(f"Invalid tool_mappings: {err}") from err
        if self.skill_order is not None:
            parsed_orders: List[SkillOrderItem] = []
            for item in self.skill_order:
                if isinstance(item, dict):
                    parsed_orders.append(SkillOrderItem(**item))
                elif isinstance(item, SkillOrderItem):
                    parsed_orders.append(item)
                else:
                    raise ValidationError(f"Invalid skill_order item: {item!r}")
            self.skill_order = parsed_orders
        if isinstance(self.runtime_conventions, dict):
            try:
                self.runtime_conventions = RuntimeConventions(**self.runtime_conventions)
            except TypeError as err:
                raise ValidationError(f"Invalid runtime_conventions: {err}") from err

    def validate(self) -> None:
        if not is_valid_host_id(self.host):
            raise ValidationError(f"Unknown host: {self.host!r}")
        if self.support_state not in SUPPORT_STATES:
            raise ValidationError(f"Invalid support state: {self.support_state!r}")
        if not self.skills_dir:
            raise ValidationError(f"Harness profile for {self.host} must declare a non-empty skills_dir")
        if not self.plugin_manifest:
            raise ValidationError(f"Harness profile for {self.host} must declare a plugin_manifest")

        # Domain Rule: a declared host is not a supported one (#446). Its profile may
        # describe the adapter, but the declaration itself proves nothing: a support
        # state above `candidate` or a `verified` capability row would be a promotion
        # off the declaration, so both fail closed. Native evidence is the only way
        # up, and it is read through the same receipt gates as any built-in host. The
        # legacy aliases walk this gate too - `custom` and `claude` are declarations
        # without native support, not built-ins.
        if is_declared_host(self.host):
            if self.support_state != "candidate":
                raise ValidationError(
                    f"Declared host {self.host!r} must stay candidate until native evidence proves it, "
                    f"not {self.support_state!r}"
                )
            for declared in self.bindings:
                if declared.verification_status == "verified":
                    raise ValidationError(
                        f"Declared host {self.host!r} cannot mark {declared.capability} verified "
                        "without native evidence"
                    )

        for b in self.bindings:
            b.validate()
        for e in self.evidence_ledger:
            e.validate()

        # Domain Rule: one binding per capability. Every reader indexes the bindings as
        # `{b.capability: b}`, so a second row for one capability collapses last-wins and
        # the dropped row's evidence stops being read. A profile that binds one capability
        # twice never has a well-defined verdict, so it fails closed here (#473).
        caps = [b.capability for b in self.bindings]
        duplicates = sorted({c for c in caps if caps.count(c) > 1})
        if duplicates:
            raise ValidationError(
                f"Harness profile for {self.host} binds a capability more than once: {duplicates}"
            )
        if self.package_descriptor:
            self.package_descriptor.validate()

        # Domain Rule: Supported/verified state requires all 17 capabilities in PORTABLE_CAPABILITY_UNIVERSE to be explicitly classified
        if self.support_state in ("supported", "verified"):
            bound_caps = {b.capability: b for b in self.bindings}
            missing_universe = set(PORTABLE_CAPABILITY_UNIVERSE) - set(bound_caps.keys())
            if missing_universe:
                raise ValidationError(
                    f"{self.support_state.title()} harness profile for {self.host} must explicitly classify all 17 portable capabilities (missing: {sorted(missing_universe)})"
                )

            for req in MANDATORY_SUPPORT_FLOOR:
                binding = bound_caps[req]
                if binding.implementation_status == "gap" and req != "workspace.readonly":
                    raise ValidationError(
                        f"{self.support_state.title()} harness {self.host} cannot have gap on mandatory capability {req}"
                    )
                if self.support_state == "supported" and binding.verification_status != "verified":
                    raise ValidationError(
                        f"Supported harness {self.host} has unverified mandatory capability {req}: {binding.verification_status}"
                    )

        # Domain Rule: Harness tool mappings are structured and schema-validated
        if self.tool_mappings is not None:
            self.tool_mappings.validate()

        # Domain Rule: Skill order resolution follows a declared 3-tier fallback matrix
        if self.skill_order is not None:
            for item in self.skill_order:
                item.validate()

        # Domain Rule: Harness runtime conventions are structured and schema-validated
        if self.runtime_conventions is not None:
            self.runtime_conventions.validate()

    def validate_evidence(
        self,
        root: Path,
        check_freshness: bool = True,
        current_revisions: Optional[SurfaceRevisions] = None,
    ) -> Dict[str, Any]:
        from scripts.evidence_durability import check_evidence_durability

        return check_evidence_durability(
            self,
            root,
            check_freshness=check_freshness,
            current_revisions=current_revisions,
        )


from scripts.surface_revisions import SurfaceRevisions


PLANE_SURFACE_DEPENDENCIES: Dict[str, Tuple[str, ...]] = {
    "canonical": (
        "canonical_pin",
        "spec_hash",
    ),
    "adapter": (
        "profile_hash",
        "driver_revision",
        "boundary_driver_revision",
    ),
    "package": (
        "package_descriptor_hash",
        "manifest_hash",
        "package_driver_revision",
    ),
    "runtime": (
        "skills_tree_hash",
        "profile_hash",
        "package_descriptor_hash",
        "manifest_hash",
        "driver_revision",
    ),
}


@dataclass
class ChildSettlement:
    """Typed child spawn/join proof. All fields required; no free-text inference."""
    child_id: str
    terminal_outcome: str  # success | error | timeout | cancelled
    model: str
    transport: str  # rpc | sdk | cli
    effective_rpc: str = ""  # effective RPC/profile config observed at spawn

    def validate(self) -> None:
        if not self.child_id:
            raise ValidationError("ChildSettlement child_id cannot be empty")
        if self.terminal_outcome not in ("success", "error", "timeout", "cancelled"):
            raise ValidationError(f"Invalid terminal_outcome: {self.terminal_outcome!r}")
        if not self.model:
            raise ValidationError("ChildSettlement model cannot be empty")
        if self.transport not in ("rpc", "sdk", "cli"):
            raise ValidationError(f"Invalid transport: {self.transport!r}")
        if not self.effective_rpc:
            raise ValidationError("ChildSettlement effective_rpc cannot be empty")


@dataclass
class ScenarioResult:
    id: str
    description: str
    plane: str  # canonical | adapter | package | runtime
    command: str
    exit_code: int
    stdout_snippet: str
    verdict: str  # PASS | FAIL | BLOCKED | UNTESTED
    duration_s: float
    evidence_level: Optional[str] = "offline"  # static | offline | observed_live | legacy
    settlement: Optional[ChildSettlement | Dict[str, Any]] = None
    preserved_from: str = ""  # run_id whose observed_live evidence this scenario carries

    def validate(self) -> None:
        if not self.id:
            raise ValidationError("ScenarioResult id cannot be empty")
        if self.plane not in CONFORMANCE_PLANES:
            raise ValidationError(f"Invalid plane: {self.plane!r}")
        if self.verdict not in ("PASS", "FAIL", "BLOCKED", "UNTESTED"):
            raise ValidationError(f"Invalid verdict: {self.verdict!r}")
        if not self.evidence_level:
            raise ValidationError(
                f"Scenario {self.id!r} records no evidence_level: every scenario must say "
                "how it was observed (static | offline | observed_live | legacy)"
            )
        if self.evidence_level not in ("static", "offline", "observed_live", "legacy"):
            raise ValidationError(f"Invalid evidence_level: {self.evidence_level!r}")
        if isinstance(self.settlement, dict):
            self.settlement = ChildSettlement(**self.settlement)
        if self.settlement is not None:
            if not isinstance(self.settlement, ChildSettlement):
                raise ValidationError(f"Invalid settlement: {self.settlement!r}")
            self.settlement.validate()


def reduce_verdicts(verdicts: Iterable[str]) -> str:
    """Reduce scenario or plane verdicts according to the strict severity lattice:
    FAIL > BLOCKED > UNTESTED > PASS.

    The single lattice: the receipt validator, the drivers' receipt assembly, the
    support-state derivation and `check-evidence` all reduce through here (#473).
    """
    v_set = set(verdicts)
    if not v_set:
        return "UNTESTED"
    if "FAIL" in v_set:
        return "FAIL"
    if "BLOCKED" in v_set:
        return "BLOCKED"
    if "UNTESTED" in v_set:
        return "UNTESTED"
    if v_set == {"PASS"}:
        return "PASS"
    return "FAIL"


def _is_observed_settlement(scenario, capability: Optional[str] = None) -> bool:
    if not (
        scenario.plane == "runtime"
        and scenario.evidence_level == "observed_live"
        and isinstance(scenario.settlement, ChildSettlement)
        and scenario.verdict == "PASS"
    ):
        return False
    outcome = scenario.settlement.terminal_outcome
    if outcome == "success":
        return True
    return capability is not None and outcome in SETTLEMENT_PROMOTIONS.get(capability, ())


def settle_planes(scenarios: Iterable[ScenarioResult]) -> Dict[str, str]:
    """Reduce every conformance plane, gating a runtime PASS on a live settlement.

    A runtime PASS is a live claim: it needs at least one runtime scenario carrying a
    typed child spawn/join settlement. Offline scenario checks (route, config, doctor)
    prove the wiring, not a running child, so a settlement-free runtime plane is
    UNTESTED and never promotes the host. FAIL and BLOCKED are findings in their own
    right and pass through untouched (#444).

    Every path that can add or restore a scenario reduces through here. Preservation
    puts a live settlement back into the scenario list, so a plane reduced before it
    claims a live observation the receipt's own rows contradict (#322, #444).
    `VerificationReceipt.validate` reduces through it too, so declared planes cannot
    float free of the scenarios that are supposed to prove them (#473).
    """
    scenarios = list(scenarios)
    planes = {
        plane: reduce_verdicts(s.verdict for s in scenarios if s.plane == plane)
        for plane in CONFORMANCE_PLANES
    }
    runtime = [s for s in scenarios if s.plane == "runtime"]
    for s in runtime:
        # A driver hands its settlement back as a plain dict; type it the way
        # ScenarioResult.validate does so the gate reads the same shape.
        if isinstance(s.settlement, dict):
            s.settlement = ChildSettlement(**s.settlement)
    if planes["runtime"] == "PASS" and not any(_is_observed_settlement(s) for s in runtime):
        planes["runtime"] = "UNTESTED"
    return planes


@dataclass
class VerificationReceipt:
    run_id: str
    host: str
    host_version: str
    timestamp: str
    overall_verdict: str
    planes: Dict[str, str]
    surface_revisions: SurfaceRevisions | Dict[str, str]
    scenarios: List[ScenarioResult | Dict[str, Any]] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    claim: Optional[str] = None
    kind: Optional[str] = "runtime"
    # Exact adapter build the evidence was produced by. Optional for the built-in
    # six; a declared host has to name it before its receipt can be read (#446).
    adapter_version: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.surface_revisions, dict):
            self.surface_revisions = SurfaceRevisions(**self.surface_revisions)
        parsed_scenarios: List[ScenarioResult] = []
        for s in self.scenarios:
            if isinstance(s, dict):
                parsed_scenarios.append(ScenarioResult(**s))
            elif isinstance(s, ScenarioResult):
                parsed_scenarios.append(s)
            else:
                raise ValidationError(f"Invalid scenario item: {s!r}")
        self.scenarios = parsed_scenarios

    def validate(self) -> None:
        if not self.run_id:
            raise ValidationError("run_id cannot be empty")
        if not is_valid_receipt_host(self.host):
            raise ValidationError(f"Unknown host: {self.host!r}")
        if not self.host_version:
            raise ValidationError("host_version cannot be empty")
        # A declared host's identity names a namespace (or a pre-registry alias),
        # not a build (#446). Without the exact adapter version this receipt cannot
        # say what produced it, so it refuses to be read: the row citing it proves
        # nothing and the host stays candidate/GAP rather than being promoted off an
        # unattributed observation.
        if is_declared_host(self.host) and not self.adapter_version:
            raise ValidationError(
                f"Receipt for declared host {self.host!r} must name the adapter_version it was produced by"
            )
        if self.overall_verdict not in ("PASS", "FAIL", "BLOCKED", "UNTESTED"):
            raise ValidationError(f"Invalid overall_verdict: {self.overall_verdict!r}")
        for p, v in self.planes.items():
            if p not in CONFORMANCE_PLANES:
                raise ValidationError(f"Unknown plane: {p!r}")
            if v not in ("PASS", "FAIL", "UNTESTED", "BLOCKED"):
                raise ValidationError(f"Invalid plane verdict: {v!r}")
        for s in self.scenarios:
            s.validate()
        # A receipt must be evidence-shaped before any bar reads it: the planes it
        # declares are the reduction of the scenarios supposed to prove them, and the
        # overall verdict is the reduction of those planes. Without this, hand-written
        # or foreign bytes can declare a plane the run never observed and outvote the
        # scenarios that contradict it (#473).
        declared = settle_planes(self.scenarios)
        if self.planes != declared:
            raise ValidationError(
                f"Declared planes {self.planes!r} are not the scenario reduction {declared!r}: "
                "a plane must be proved by its own scenarios"
            )
        reduced_overall = reduce_verdicts(declared.values())
        if self.overall_verdict != reduced_overall:
            raise ValidationError(
                f"overall_verdict {self.overall_verdict!r} is not the reduction of its "
                f"planes ({reduced_overall!r})"
            )

    def evaluate_plane_staleness(self, current_revisions: SurfaceRevisions) -> Dict[str, List[str]]:
        reasons: Dict[str, List[str]] = {p: [] for p in CONFORMANCE_PLANES}
        receipt_dict = self.surface_revisions.to_dict()
        current_dict = current_revisions.to_dict()
        for plane, deps in PLANE_SURFACE_DEPENDENCIES.items():
            for dep in deps:
                rec_val = receipt_dict.get(dep)
                curr_val = current_dict.get(dep)
                if not rec_val:
                    reasons[plane].append(f"missing {dep} in receipt")
                elif rec_val != curr_val:
                    reasons[plane].append(
                        f"{dep} mismatch (receipt={rec_val[:8]}..., current={curr_val[:8]}...)"
                    )
        return reasons


from scripts.surface_revisions import (
    DOCSTRING_CONSUMED_DRIVERS,
    RecipeError,
    _DRIVER_CORE_CACHE_MAX_BYTES,
    _DRIVER_CORE_CACHE_MAX_RECORDS,
    _DRIVER_CORE_CACHE_VERSION,
    _DRIVER_CORE_MEMO,
    _driver_core,
    _driver_core_cache_dir,
    _module_docstring,
    _prune_driver_core_cache,
    _read_driver_core_cache,
    _strip_docstrings,
    _update_driver_digest,
    _write_driver_core_cache,
    compute_surface_revisions,
)
_EVIDENCE_DURABILITY_SYMBOLS = {
    "_is_preservable_settlement",
    "_row_level",
    "_row_receipt",
    "check_evidence_durability",
    "check_scenario_pins",
    "derive_support_state",
    "preserve_observed_settlements",
}


def __getattr__(name: str) -> Any:
    if name in _EVIDENCE_DURABILITY_SYMBOLS:
        import scripts.evidence_durability as _ed

        val = getattr(_ed, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(list(globals().keys()) + list(_EVIDENCE_DURABILITY_SYMBOLS))
