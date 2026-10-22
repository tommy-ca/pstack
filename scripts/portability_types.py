"""Domain types, dataclasses, and reduction logic for pstack portability.

Separated from portability_schema.py for modular decomposition (#603).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from scripts.host_identity import (
    KNOWN_HOSTS,
    is_declared_host,
    is_valid_host_id,
    is_valid_receipt_host,
    require_builtin_host_keys,
)
from scripts.surface_revisions import SurfaceRevisions

SUPPORT_STATES = ("candidate", "mapped", "packaged", "verified", "supported")
IMPLEMENTATION_STATUSES = ("native", "shim", "version-gated", "gap")
ENFORCEMENT_LEVELS = ("hard", "soft", "advisory")
VERIFICATION_STATUSES = ("verified", "static-only", "unverified", "stale")
ADAPTATION_MODES = ("preserve", "adapt", "exclude", "gap")
HOSTS = KNOWN_HOSTS
CONFORMANCE_PLANES = ("canonical", "adapter", "package", "runtime")

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

require_builtin_host_keys(DEFAULT_SKILLS_DIRS, "DEFAULT_SKILLS_DIRS")
require_builtin_host_keys(DEFAULT_PLUGIN_MANIFESTS, "DEFAULT_PLUGIN_MANIFESTS")


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
        if isinstance(self.evidence_ref, dict):
            return self.evidence_ref.get("receipt")
        return self.evidence_ref

    @property
    def scenario_id(self) -> Optional[str]:
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

        for field_name in FORBIDDEN_ORCHESTRATION_FIELDS:
            if field_name in self.raw_dict:
                raise ValidationError(
                    f"Package descriptor must not encode runtime orchestration semantics: {field_name}"
                )





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

        caps = [b.capability for b in self.bindings]
        duplicates = sorted({c for c in caps if caps.count(c) > 1})
        if duplicates:
            raise ValidationError(
                f"Harness profile for {self.host} binds a capability more than once: {duplicates}"
            )
        if self.package_descriptor:
            self.package_descriptor.validate()

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

        if self.tool_mappings is not None:
            self.tool_mappings.validate()

        if self.skill_order is not None:
            for item in self.skill_order:
                item.validate()

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
    child_id: str
    terminal_outcome: str
    model: str
    transport: str
    effective_rpc: str = ""

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
    plane: str
    command: str
    exit_code: int
    stdout_snippet: str
    verdict: str
    duration_s: float
    evidence_level: Optional[str] = "offline"
    settlement: Optional[ChildSettlement | Dict[str, Any]] = None
    preserved_from: str = ""
    live_attempted: bool = False

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
    scenarios = list(scenarios)
    planes = {
        plane: reduce_verdicts(s.verdict for s in scenarios if s.plane == plane)
        for plane in CONFORMANCE_PLANES
    }
    runtime = [s for s in scenarios if s.plane == "runtime"]
    for s in runtime:
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
