"""Typed validation and domain model for pstack portability.

Implements the domain rules defined in openspec/specs/pstack-portability/spec.md
and issues #50 and #76. Pure Python with zero external dependencies.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
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
        return check_evidence_durability(
            self,
            root,
            check_freshness=check_freshness,
            current_revisions=current_revisions,
        )


@dataclass
class SurfaceRevisions:
    canonical_pin: str
    upstream_head: str
    spec_hash: str
    skills_tree_hash: str
    profile_hash: str
    package_descriptor_hash: str
    manifest_hash: str
    driver_revision: str
    package_driver_revision: str
    boundary_driver_revision: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


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


class RecipeError(RuntimeError):
    """The driver-fingerprint recipe refused to produce a revision (fail closed)."""


# Drivers that publish their own module docstring at runtime
# (`argparse.ArgumentParser(description=__doc__)`): that text is observable
# behaviour, so it contributes raw on top of the behaviour-bearing core.
DOCSTRING_CONSUMED_DRIVERS = (
    "canonical-index.py",
    "verify-portable.py",
    # Skills CLIs publishing `__doc__` as `--help` (F3, #444): a docstring edit
    # changes user-visible output, so the fingerprint keeps it.
    "pack.py",
    "partition.py",
    "apply.py",
    "refresh-hygiene.py",
)


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    """Drop every module/class/function docstring from `tree` in place."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]
    return tree


def _module_docstring(tree: ast.AST) -> bytes:
    body = getattr(tree, "body", [])
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[0].value.value.encode("utf-8")
    return b""


def _update_driver_digest(hasher: Any, path: Path) -> None:
    """Fold `path` into `hasher` as its behaviour-bearing core.

    The core is `ast.unparse` of the parsed module with docstrings stripped, so a
    comment, docstring, blank line or reformat cannot move a revision — only an
    edit the AST can carry does (#444). A file that will not parse raises
    `RecipeError` rather than silently degrading to a whole-file byte hash, and
    a `DOCSTRING_CONSUMED_DRIVERS` module contributes its published module
    docstring raw because the core would drop it.
    """
    src = path.read_bytes()
    try:
        tree = ast.parse(src.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError) as err:
        raise RecipeError(f"unparseable driver {path}: {err}") from err
    # Read the published docstring before stripping: the strip mutates the tree.
    published = _module_docstring(tree) if path.name in DOCSTRING_CONSUMED_DRIVERS else b""
    hasher.update(ast.unparse(_strip_docstrings(tree)).encode("utf-8"))
    hasher.update(published)


def compute_surface_revisions(root: Path, host: str, profile_path: Optional[Path] = None) -> SurfaceRevisions:
    # 1. canonical pin
    upstream_file = root / "UPSTREAM"
    canonical_pin = "unknown"
    if upstream_file.is_file():
        m = re.search(r"^tree ([0-9a-f]{40})$", upstream_file.read_text(encoding="utf-8"), re.M)
        if m:
            canonical_pin = m.group(1)

    # 2. upstream head
    inv_file = root / "openspec" / "canonical-inventory.json"
    upstream_head = "unknown"
    if inv_file.is_file():
        try:
            inv = json.loads(inv_file.read_text(encoding="utf-8"))
            upstream_head = inv.get("upstream_head", "unknown")
        except Exception:
            pass

    # 3. spec hash
    spec_file = root / "openspec" / "specs" / "pstack-portability" / "spec.md"
    spec_hash = hashlib.sha256(spec_file.read_bytes()).hexdigest() if spec_file.is_file() else "missing"

    # 4. skills tree hash — prose raw, Python by its behaviour-bearing core.
    # A skill script is code, so a comment inside it must not cost a five-host
    # re-proof any more than a comment inside a driver does (#444); a statement
    # the AST can carry still moves the revision.
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        hasher = hashlib.sha256()
        for p in sorted(skills_dir.rglob("*")):
            rel = p.relative_to(skills_dir)
            if any(part in SKILLS_HASH_IGNORED_DIRS for part in rel.parts):
                continue
            if p.is_file():
                if p.suffix in SKILLS_HASH_IGNORED_SUFFIXES:
                    continue
                hasher.update(rel.as_posix().encode("utf-8"))
                if p.suffix == ".py":
                    try:
                        _update_driver_digest(hasher, p)
                    except RecipeError as err:
                        # F2 (#444): an upstream-shaped skills script that will not
                        # parse is data, not a local edit. Fail closed per file so
                        # the matrix still reports every other host instead of
                        # aborting the whole run on one row. The mark is the
                        # stable error category plus the file bytes: never the
                        # exception string, which carries the absolute root path
                        # and would fingerprint the same bad file differently in
                        # the checkout, a pytest copy, and CI.
                        category = type(err.__cause__).__name__ if err.__cause__ else type(err).__name__
                        hasher.update(f"recipe-error:{category}:".encode("utf-8"))
                        hasher.update(hashlib.sha256(p.read_bytes()).digest())
                else:
                    hasher.update(p.read_bytes())
        skills_tree_hash = hasher.hexdigest()
    else:
        skills_tree_hash = "missing"

    # 5. profile hash
    if profile_path is None:
        profile_path = root / "profiles" / f"{host}.json"
    if profile_path.is_file():
        try:
            profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
            profile_hash = hashlib.sha256(
                json.dumps(profile_data, sort_keys=True, indent=2).encode("utf-8")
            ).hexdigest()
        except Exception:
            profile_hash = hashlib.sha256(profile_path.read_bytes()).hexdigest()
    else:
        profile_hash = "missing"

    # 6. package descriptor hash
    pkg_file = root / "pstack.package.json"
    if pkg_file.is_file():
        try:
            pkg_data = json.loads(pkg_file.read_text(encoding="utf-8"))
            package_descriptor_hash = hashlib.sha256(
                json.dumps(pkg_data, sort_keys=True, indent=2).encode("utf-8")
            ).hexdigest()
        except Exception:
            package_descriptor_hash = hashlib.sha256(pkg_file.read_bytes()).hexdigest()
    else:
        package_descriptor_hash = "missing"

    # 7. manifest hash
    manifest_rel = DEFAULT_PLUGIN_MANIFESTS.get(host)
    if profile_path.is_file():
        try:
            pdata = json.loads(profile_path.read_text(encoding="utf-8"))
            if pdata.get("plugin_manifest"):
                manifest_rel = pdata["plugin_manifest"]
        except Exception:
            pass
    manifest_file = root / manifest_rel if manifest_rel else None
    if manifest_file and manifest_file.is_file():
        try:
            man_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            manifest_hash = hashlib.sha256(
                json.dumps(man_data, sort_keys=True, indent=2).encode("utf-8")
            ).hexdigest()
        except Exception:
            manifest_hash = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
    else:
        manifest_hash = "missing"

    # 8. driver revision — the behaviour-bearing core of each driver, not its
    # whole-file bytes: a comment must not cost a five-host re-proof (#444).
    hasher = hashlib.sha256()
    for fname in (
        "canonical-index.py",
        "verify-portable.py",
        "verify-harness.py",
        "adapt-harness.py",
        "scaffold-verification-skill.py",
        "skill_frontmatter.py",
        "host_identity.py",
        "portability_schema.py",
        "route_resolver.py",
    ):
        driver_file = root / "scripts" / fname
        if driver_file.is_file():
            hasher.update(fname.encode("utf-8"))
            _update_driver_digest(hasher, driver_file)
    drivers_dir = root / "scripts" / "drivers"
    if drivers_dir.is_dir():
        for p in sorted(drivers_dir.rglob("*.py")):
            hasher.update(p.relative_to(drivers_dir).as_posix().encode("utf-8"))
            _update_driver_digest(hasher, p)
    driver_revision = hasher.hexdigest()

    # 9. package driver revision
    pkg_hasher = hashlib.sha256()
    for fname in ("project-package.py", "package-lifecycle.py", "sync-antigravity-plugin.py"):
        p = root / "scripts" / fname
        if p.is_file():
            pkg_hasher.update(fname.encode("utf-8"))
            _update_driver_digest(pkg_hasher, p)
    package_driver_revision = pkg_hasher.hexdigest()

    # 10. boundary driver revision
    bnd_driver_file = root / "scripts" / "scan-host-boundary.py"
    if bnd_driver_file.is_file():
        bnd_hasher = hashlib.sha256()
        _update_driver_digest(bnd_hasher, bnd_driver_file)
        boundary_driver_revision = bnd_hasher.hexdigest()
    else:
        boundary_driver_revision = "missing"

    return SurfaceRevisions(
        canonical_pin=canonical_pin,
        upstream_head=upstream_head,
        spec_hash=spec_hash,
        skills_tree_hash=skills_tree_hash,
        profile_hash=profile_hash,
        package_descriptor_hash=package_descriptor_hash,
        manifest_hash=manifest_hash,
        driver_revision=driver_revision,
        package_driver_revision=package_driver_revision,
        boundary_driver_revision=boundary_driver_revision,
    )
def _is_observed_settlement(scenario, capability: Optional[str] = None) -> bool:
    """True only for a passing runtime observed_live scenario carrying a typed settlement.

    A settlement that records an error or timeout proves the child did not spawn and join,
    so it never satisfies the promotion gate. A typed cancellation is the opposite for
    `agent.cancel`: the cancellation *is* what that capability exists to prove, so the
    outcome it may pin is listed in SETTLEMENT_PROMOTIONS (#381). Every other capability
    still needs the successful spawn/join settlement, and a caller holding no capability
    (support-state derivation, receipt preservation) sees only that unconditional shape.
    """
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


def _is_preservable_settlement(scenario) -> bool:
    """Any live typed settlement a pinned row may read, whoever pinned it.

    preserve_observed_settlements works by scenario id and holds no profile, so it must
    treat a settled cancellation as carryable evidence too: otherwise a route-free refresh
    drops the scenario `agent.cancel` pins and turns that pin into a hard error (#322).
    """
    return _is_observed_settlement(scenario) or any(
        _is_observed_settlement(scenario, capability) for capability in SETTLEMENT_PROMOTIONS
    )

def preserve_observed_settlements(
    previous: VerificationReceipt,
    current: VerificationReceipt,
) -> List[str]:
    """Carry a prior observed_live settlement into a run that could not observe one.

    A model-route-free refresh restates every scenario as static evidence. Writing that
    over the durable receipt deletes the only settlement the OMP promotion gate reads,
    demoting the host for a reason unrelated to the change being made (#322). Carry the
    prior scenario forward while the runtime surface it proved is unchanged, mark the run
    it came from, and drop it the moment that surface moves so the demotion stays honest.
    """
    if previous.host != current.host:
        return []
    # validate() types a JSON round-tripped settlement; _is_observed_settlement
    # requires a ChildSettlement instance, not the raw dict.
    previous.validate()
    current.validate()
    if previous.evaluate_plane_staleness(current.surface_revisions).get("runtime"):
        return []
    prior = {s.id: s for s in previous.scenarios if _is_preservable_settlement(s)}
    preserved: List[str] = []
    for i, scenario in enumerate(current.scenarios):
        candidate = prior.get(scenario.id)
        if candidate is None or _is_preservable_settlement(scenario) or scenario.verdict != "PASS":
            continue
        current.scenarios[i] = replace(candidate, preserved_from=candidate.preserved_from or previous.run_id)
        preserved.append(scenario.id)
    return preserved


def _row_receipt(binding: Binding, root: Path) -> Optional[VerificationReceipt]:
    """The receipt a row cites, or None when the row cannot be read at all.

    A row that is not `verified`, cites nothing, cites a file that is not on disk, or
    cites bytes that are not a valid receipt proves nothing. Both levels ask that same
    question of a row, so the read lives here once.
    """
    if binding.verification_status != "verified":
        return None
    if not binding.receipt_ref or not (root / binding.receipt_ref).is_file():
        return None
    try:
        receipt = VerificationReceipt(
            **json.loads((root / binding.receipt_ref).read_text(encoding="utf-8"))
        )
        receipt.validate()
    except Exception:
        return None
    return receipt


def _row_level(
    receipt: Optional[VerificationReceipt],
    profile: HarnessProfile,
    current_revisions: SurfaceRevisions,
    *,
    require_package: bool,
) -> str:
    """The level one row proves: '' (nothing), 'verified' (the floor bar) or 'supported'.

    One row bar for both levels (#473). `require_package` is the only thing separating
    them — the floor is runtime plus canonical/adapter PASS, fresh against
    `current_revisions`, plus the OMP settlement bar; `supported` adds the package plane —
    so `supported ⇒ verified` is structural instead of a second copy of the clauses that
    can drift from this one.
    """
    if receipt is None or receipt.host != profile.host:
        return ""
    # The live plane is what both levels rest on; `package` is what `supported` adds.
    rest = ("canonical", "adapter", "package") if require_package else ("canonical", "adapter")
    if receipt.planes.get("runtime") != "PASS" or any(
        receipt.planes.get(p) != "PASS" for p in rest
    ):
        return ""
    # Staleness over the planes the bar asks for (all four at `supported`).
    stale = receipt.evaluate_plane_staleness(current_revisions)
    if any(stale.get(p) for p in ("runtime", *rest)):
        return ""
    # OMP only: the receipt carries evidence_level on every scenario and at least one
    # runtime-plane scenario observed_live carrying structured settlement evidence (child
    # identity plus terminal outcome). OMP offline-only receipts prove at most 'packaged':
    # the OMP driver never observed a child spawn/join, a live canonical check cannot
    # stand in for it, and a bare observed_live label without settlement markers is
    # relabel fraud, not proof. Other hosts keep their existing contract until their own
    # leaf proves the same bar.
    if profile.host == "omp" and (
        any(not s.evidence_level for s in receipt.scenarios)
        or not any(_is_observed_settlement(s) for s in receipt.scenarios)
    ):
        return ""
    return "supported" if require_package else "verified"


def derive_support_state(
    profile: HarnessProfile,
    root: Path,
    current_revisions: Optional[SurfaceRevisions] = None,
) -> str:
    """Mechanically derive the support state proved by durable evidence."""
    # Direct callers (tests, tooling) get the same domain rules the CLI paths run: a
    # profile that binds a capability twice has no defined verdict (#473).
    profile.validate()
    bound_caps = {b.capability: b for b in profile.bindings}
    if not bound_caps or any(c not in bound_caps for c in PORTABLE_CAPABILITY_UNIVERSE):
        return "candidate"

    if current_revisions is None:
        current_revisions = compute_surface_revisions(root, profile.host)

    # Level: mapped
    if profile.tool_mappings is None or profile.runtime_conventions is None:
        return "mapped"

    # Level: packaged
    if not profile.plugin_manifest or not (root / profile.plugin_manifest).is_file():
        return "mapped"
    if not (root / "pstack.package.json").is_file():
        return "mapped"

    # Level: verified — the nine mandatory capabilities are rows like any other, and
    # every one of them has to clear the floor bar `_row_level` defines: a `verified`
    # row citing a readable receipt of this host (canonical+adapter+runtime PASS and
    # fresh) plus the OMP settlement bar. The floor declares the bar, not a copy of it.
    for cap_id in MANDATORY_SUPPORT_FLOOR:
        if _row_level(
            _row_receipt(bound_caps[cap_id], root),
            profile,
            current_revisions,
            require_package=False,
        ) != "verified":
            return "packaged"

    # Level: supported — the same rows, the same one bar, plus the package plane. The
    # conditional rows cannot claim the level above `verified` off a package-only PASS
    # while their behavioral planes FAIL, and every row is checked, not just the floor.
    for binding in bound_caps.values():
        if _row_level(
            _row_receipt(binding, root),
            profile,
            current_revisions,
            require_package=True,
        ) != "supported":
            return "verified"

    return "supported"


def check_scenario_pins(
    profile: HarnessProfile, receipts_by_ref: Dict[str, VerificationReceipt]
) -> None:
    """Resolve every scenario-pinned binding against the receipt it cites.

    A pin naming a scenario its receipt does not record is a dangling reference. A
    `verified` row must pin the observed_live settlement the spec requires before a
    live behavior may be claimed; a weaker scenario belongs to a `static-only` row.
    Receipt-only (bare path) references keep their existing contract and resolve by
    path alone.
    """
    for binding in profile.bindings:
        scenario_id = binding.scenario_id
        if not scenario_id:
            continue
        receipt = receipts_by_ref.get(binding.receipt_ref or "")
        if receipt is None:
            raise ValidationError(
                f"Dangling evidence path for {profile.host}: {binding.receipt_ref}"
            )
        scenario = next((s for s in receipt.scenarios if s.id == scenario_id), None)
        if scenario is None:
            raise ValidationError(
                f"Binding for {binding.capability} on {binding.host} cites scenario {scenario_id!r}, "
                f"which {binding.receipt_ref} does not record"
            )
        if binding.verification_status == "verified" and not _is_observed_settlement(
            scenario, binding.capability
        ):
            raise ValidationError(
                f"Binding for {binding.capability} on {binding.host} claims verified but scenario "
                f"{scenario_id!r} carries no observed_live settlement (evidence_level="
                f"{scenario.evidence_level!r}, verdict={scenario.verdict!r}); restore the live proof "
                "(omp: PSTACK_RUN_OMP_LIVE=1) or record the row as static-only"
            )


def check_evidence_durability(
    profile: HarnessProfile,
    root: Path,
    check_freshness: bool = True,
    current_revisions: Optional[SurfaceRevisions] = None,
) -> Dict[str, Any]:
    """Check that all evidence references exist, receipts are valid, and support state is derived."""
    # `doctor` already validates the profile in its subprocess; this is the same gate on
    # the in-process path, so `check-evidence` judges the file it read, not a looser copy
    # of it (#473).
    profile.validate()
    refs = {b.receipt_ref for b in profile.bindings if b.receipt_ref}
    refs.update(e.artifact for e in profile.evidence_ledger if e.artifact)

    if profile.support_state in ("verified", "supported") and not refs:
        raise ValidationError(
            f"Harness profile for {profile.host} claims {profile.support_state} but declares no evidence references"
        )

    receipts_by_ref: Dict[str, VerificationReceipt] = {}
    for ref in sorted(refs):
        path = root / ref
        if not path.is_file():
            raise ValidationError(
                f"Dangling evidence path for {profile.host}: {ref}"
            )
        try:
            rdata = json.loads(path.read_text(encoding="utf-8"))
            receipt = VerificationReceipt(**rdata)
            receipt.validate()
        except Exception as err:
            raise ValidationError(
                f"Evidence file {ref} for {profile.host} is not a valid VerificationReceipt: {err}"
            ) from err

        if receipt.host != profile.host:
            raise ValidationError(
                f"Evidence file {ref} host mismatch: expected {profile.host}, got {receipt.host}"
            )
        receipts_by_ref[ref] = receipt

    if current_revisions is None:
        current_revisions = compute_surface_revisions(root, profile.host)

    staleness_by_ref: Dict[str, Dict[str, List[str]]] = {}
    for ref, receipt in receipts_by_ref.items():
        staleness_by_ref[ref] = receipt.evaluate_plane_staleness(current_revisions)

    derived_state = derive_support_state(profile, root, current_revisions=current_revisions)

    # Pin violations name their remedy; staleness is reported after, so a bad
    # claim points at the claim first (see
    # test_check_evidence_names_the_omp_live_remedy).
    check_scenario_pins(profile, receipts_by_ref)

    if check_freshness:
        # Freshness planes follow the claimed level cumulatively: `packaged` proves
        # the package plane, and every level above it keeps that plane while adding
        # the behavioral ones. `verified` used to check canonical/adapter/runtime
        # only, so a stale package driver passed a claim one rung above `packaged`,
        # which does check it (#473). Candidate claims skip the gate.
        if profile.support_state in ("verified", "supported", "packaged"):
            stale_details: List[str] = []
            if profile.support_state == "packaged":
                freshness_planes = ("package",)
            else:
                freshness_planes = ("canonical", "adapter", "runtime", "package")
            for b in profile.bindings:
                if b.capability in MANDATORY_SUPPORT_FLOOR:
                    if b.receipt_ref and b.receipt_ref in staleness_by_ref:
                        s_map = staleness_by_ref[b.receipt_ref]
                        for plane in freshness_planes:
                            if s_map.get(plane):
                                stale_details.append(f"{b.capability} ({plane}): {', '.join(s_map[plane])}")
            if stale_details:
                raise ValidationError(
                    f"Profile {profile.host} evidence is stale for claimed {profile.support_state}: {'; '.join(stale_details[:5])}"
                )
        claimed_idx = SUPPORT_STATES.index(profile.support_state)
        derived_idx = SUPPORT_STATES.index(derived_state)
        if claimed_idx > derived_idx:
            raise ValidationError(
                f"Hand-authored support state {profile.support_state!r} for {profile.host} exceeds "
                f"evidence-derived support state {derived_state!r}."
            )


    return {
        "valid": True,
        "host": profile.host,
        "claimed_support_state": profile.support_state,
        "derived_support_state": derived_state,
        "receipts_checked": len(receipts_by_ref),
        "staleness": staleness_by_ref,
    }
