"""Typed validation and domain model for pstack portability.

Implements the domain rules defined in openspec/specs/pstack-portability/spec.md
and issues #50 and #76. Pure Python with zero external dependencies.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

SUPPORT_STATES = ("candidate", "mapped", "packaged", "verified", "supported")
IMPLEMENTATION_STATUSES = ("native", "shim", "version-gated", "gap")
ENFORCEMENT_LEVELS = ("hard", "soft", "advisory")
VERIFICATION_STATUSES = ("verified", "static-only", "unverified", "stale")
ADAPTATION_MODES = ("preserve", "adapt", "exclude", "gap")
HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "droid", "claude", "custom")

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
    evidence_ref: Optional[str] = None
    notes: Optional[str] = None

    def validate(self) -> None:
        if self.host not in HOSTS:
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
    "droid": ".factory/skills",
}

DEFAULT_PLUGIN_MANIFESTS = {
    "grok": ".grok-plugin/plugin.json",
    "codex": ".codex-plugin/plugin.json",
    "omp": ".omp-plugin/plugin.json",
    "opencode": ".opencode-plugin/package.json",
    "antigravity": ".antigravity-plugin/plugin.json",
    "droid": ".factory-plugin/plugin.json",
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
class ScenarioResult:
    id: str
    description: str
    plane: str  # canonical | adapter | package | runtime
    command: str
    exit_code: int
    stdout_snippet: str
    verdict: str  # PASS | FAIL | BLOCKED
    duration_s: float

    def validate(self) -> None:
        if not self.id:
            raise ValidationError("ScenarioResult id cannot be empty")
        if self.plane not in CONFORMANCE_PLANES:
            raise ValidationError(f"Invalid plane: {self.plane!r}")
        if self.verdict not in ("PASS", "FAIL", "BLOCKED"):
            raise ValidationError(f"Invalid verdict: {self.verdict!r}")


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
        if self.host not in HOSTS and self.host != "mock":
            raise ValidationError(f"Unknown host: {self.host!r}")
        if not self.host_version:
            raise ValidationError("host_version cannot be empty")
        if self.overall_verdict not in ("PASS", "FAIL", "BLOCKED"):
            raise ValidationError(f"Invalid overall_verdict: {self.overall_verdict!r}")
        for p, v in self.planes.items():
            if p not in CONFORMANCE_PLANES:
                raise ValidationError(f"Unknown plane: {p!r}")
            if v not in ("PASS", "FAIL", "UNTESTED", "BLOCKED"):
                raise ValidationError(f"Invalid plane verdict: {v!r}")
        for s in self.scenarios:
            s.validate()

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

    # 4. skills tree hash
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

    # 8. driver revision
    hasher = hashlib.sha256()
    for fname in (
        "canonical-index.py",
        "verify-portable.py",
        "verify-harness.py",
        "adapt-harness.py",
        "scaffold-verification-skill.py",
        "skill_frontmatter.py",
        "portability_schema.py",
    ):
        driver_file = root / "scripts" / fname
        if driver_file.is_file():
            hasher.update(fname.encode("utf-8"))
            hasher.update(driver_file.read_bytes())
    drivers_dir = root / "scripts" / "drivers"
    if drivers_dir.is_dir():
        for p in sorted(drivers_dir.rglob("*.py")):
            hasher.update(p.relative_to(drivers_dir).as_posix().encode("utf-8"))
            hasher.update(p.read_bytes())
    driver_revision = hasher.hexdigest()

    # 9. package driver revision
    pkg_hasher = hashlib.sha256()
    for fname in ("project-package.py", "package-lifecycle.py", "sync-antigravity-plugin.py"):
        p = root / "scripts" / fname
        if p.is_file():
            pkg_hasher.update(fname.encode("utf-8"))
            pkg_hasher.update(p.read_bytes())
    package_driver_revision = pkg_hasher.hexdigest()

    # 10. boundary driver revision
    bnd_driver_file = root / "scripts" / "scan-host-boundary.py"
    boundary_driver_revision = hashlib.sha256(bnd_driver_file.read_bytes()).hexdigest() if bnd_driver_file.is_file() else "missing"

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


def derive_support_state(
    profile: HarnessProfile,
    root: Path,
    current_revisions: Optional[SurfaceRevisions] = None,
) -> str:
    """Mechanically derive the support state proved by durable evidence."""
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

    # Level: verified
    # Requires:
    # 1. All mandatory capabilities have verification_status == "verified"
    #    (workspace.readonly can be gap/shim if soft/advisory)
    # 2. Every mandatory capability has evidence_ref pointing to an existing file
    # 3. The referenced receipt has canonical, adapter, and runtime PASS
    # 4. None of canonical, adapter, runtime planes is STALE against current_revisions
    has_mandatory_runtime_proof = True
    for cap_id in MANDATORY_SUPPORT_FLOOR:
        binding = bound_caps[cap_id]
        if binding.verification_status != "verified":
            has_mandatory_runtime_proof = False
            break
        if not binding.evidence_ref or not (root / binding.evidence_ref).is_file():
            has_mandatory_runtime_proof = False
            break
        try:
            rdata = json.loads((root / binding.evidence_ref).read_text(encoding="utf-8"))
            receipt = VerificationReceipt(**rdata)
            receipt.validate()
            if receipt.host != profile.host:
                has_mandatory_runtime_proof = False
                break
            if (
                receipt.planes.get("canonical") != "PASS"
                or receipt.planes.get("adapter") != "PASS"
                or receipt.planes.get("runtime") != "PASS"
            ):
                has_mandatory_runtime_proof = False
                break
            stale_map = receipt.evaluate_plane_staleness(current_revisions)
            if stale_map.get("canonical") or stale_map.get("adapter") or stale_map.get("runtime"):
                has_mandatory_runtime_proof = False
                break
        except Exception:
            has_mandatory_runtime_proof = False
            break

    if not has_mandatory_runtime_proof:
        return "packaged"

    # Level: supported
    # Requires verified PLUS:
    # 1. Package plane is verified with PASS and NOT STALE
    # 2. All 17 capabilities in PORTABLE_CAPABILITY_UNIVERSE have verification_status == "verified" (or valid shim/gap)
    #    with valid, non-stale receipts
    is_supported = True
    for cap_id, binding in bound_caps.items():
        if binding.verification_status != "verified":
            is_supported = False
            break
        if not binding.evidence_ref or not (root / binding.evidence_ref).is_file():
            is_supported = False
            break
        try:
            rdata = json.loads((root / binding.evidence_ref).read_text(encoding="utf-8"))
            receipt = VerificationReceipt(**rdata)
            if receipt.planes.get("package") != "PASS":
                is_supported = False
                break
            stale_map = receipt.evaluate_plane_staleness(current_revisions)
            if any(len(errs) > 0 for errs in stale_map.values()):
                is_supported = False
                break
        except Exception:
            is_supported = False
            break

    return "supported" if is_supported else "verified"


def check_evidence_durability(
    profile: HarnessProfile,
    root: Path,
    check_freshness: bool = True,
    current_revisions: Optional[SurfaceRevisions] = None,
) -> Dict[str, Any]:
    """Check that all evidence references exist, receipts are valid, and support state is derived."""
    refs = {b.evidence_ref for b in profile.bindings if b.evidence_ref}
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

    if check_freshness:
        # Check staleness based on claimed support_state
        if profile.support_state in ("verified", "supported"):
            stale_details: List[str] = []
            for b in profile.bindings:
                if b.capability in MANDATORY_SUPPORT_FLOOR:
                    if b.evidence_ref and b.evidence_ref in staleness_by_ref:
                        s_map = staleness_by_ref[b.evidence_ref]
                        for plane in ("canonical", "adapter", "runtime"):
                            if s_map.get(plane):
                                stale_details.append(f"{b.capability} ({plane}): {', '.join(s_map[plane])}")
            if profile.support_state == "supported":
                for b in profile.bindings:
                    if b.evidence_ref and b.evidence_ref in staleness_by_ref:
                        s_map = staleness_by_ref[b.evidence_ref]
                        if s_map.get("package"):
                            stale_details.append(f"{b.capability} (package): {', '.join(s_map['package'])}")

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
