#!/usr/bin/env python3
"""Host identity registry seam (#446).

One module owns the host identity set and the rule a *declared* host id must
satisfy; the ten surfaces that used to carry their own enum import it instead.
These tests pin the seam from both ends: no production surface keeps a local
enum, the JSON schemas declare exactly the module's set and pattern, and a
declared host is accepted while a collision, an unknown name and an unattributed
receipt all stay fail-closed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.host_identity import (  # noqa: E402
    BUILTIN_HOSTS,
    EXTERNAL_HOST_ID_PATTERN,
    KNOWN_HOSTS,
    LEGACY_HOST_ALIASES,
    OBSERVER_HOSTS,
    HostIdentityError,
    is_builtin,
    is_external,
    is_valid_host_id,
    is_valid_receipt_host,
    require_builtin_host_keys,
)
from scripts.portability_schema import (  # noqa: E402
    Binding,
    HarnessProfile,
    PackageDescriptor,
    ValidationError,
    VerificationReceipt,
    compute_surface_revisions,
)

SCHEMAS_DIR = ROOT / "schemas" / "portability"
HOST_ID_SCHEMA = SCHEMAS_DIR / "host-id.schema.json"

# The ten surfaces the seam replaced, as named in #446: six Python modules and
# the four host-bearing JSON schemas. Every one of them must reference the single
# source, and none of them may carry a host enum of its own.
IMPORTING_SURFACES = (
    "scripts/portability_schema.py",
    "scripts/verify-portable.py",
    "scripts/package-lifecycle.py",
    "scripts/project-package.py",
    "scripts/drivers/__init__.py",
    "scripts/scan-host-boundary.py",
)
REFERENCING_SCHEMAS = (
    "profile.schema.json",
    "binding.schema.json",
    "package-descriptor.schema.json",
    "receipt.schema.json",
)

# The shape every local copy used to have: the first two built-ins, adjacent.
LOCAL_HOST_ENUM = re.compile(r'"grok"\s*,\s*"codex"')

DECLARED = "acme:copilot"
SECOND_DECLARED = "beta:copilot"


def _load_module(name: str, rel: str):
    import importlib.util

    loader = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert loader is not None and loader.loader is not None
    module = importlib.util.module_from_spec(loader)
    sys.modules[name] = module
    loader.loader.exec_module(module)
    return module


def _registry() -> Registry:
    """Every portability schema, keyed by the `$id` its `$ref`s resolve against."""
    return Registry().with_resources(
        [
            (
                (schema := json.loads(path.read_text(encoding="utf-8")))["$id"],
                Resource.from_contents(schema),
            )
            for path in sorted(SCHEMAS_DIR.glob("*.json"))
        ]
    )


def _validator(def_name: str = "host") -> Draft202012Validator:
    """A validator for one shared host-id definition, resolved through the registry."""
    probe = {
        "$id": f"https://pstack.dev/schemas/portability/probe-{def_name}.schema.json",
        "$ref": f"host-id.schema.json#/$defs/{def_name}",
    }
    return Draft202012Validator(probe, registry=_registry())


def _declared_profile(host: str = DECLARED, support_state: str = "candidate") -> HarnessProfile:
    """A profile that declares a host the way a local adapter descriptor would."""
    slug = host.replace(":", "-")
    return HarnessProfile(
        host=host,
        support_state=support_state,
        bindings=[],
        skills_dir=f".{slug}/skills",
        plugin_manifest=f".{slug}-plugin/plugin.json",
    )


def _receipt(host: str, adapter_version=None) -> VerificationReceipt:
    return VerificationReceipt(
        run_id=f"{host}-identity-seam",
        host=host,
        host_version="1.0.0",
        timestamp="2026-10-18T00:00:00Z",
        overall_verdict="UNTESTED",
        planes={plane: "UNTESTED" for plane in ("canonical", "adapter", "package", "runtime")},
        surface_revisions=compute_surface_revisions(ROOT, host),
        scenarios=[],
        artifacts=[],
        adapter_version=adapter_version,
    )


# --- one source, ten surfaces ---------------------------------------------


def test_no_production_surface_keeps_its_own_host_enum() -> None:
    """The enum lives in exactly two files, and they are the seam and its schema."""
    offenders = []
    for base in ("scripts", "schemas"):
        for path in sorted((ROOT / base).rglob("*")):
            if path.suffix not in (".py", ".json") or not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in ("scripts/host_identity.py", "schemas/portability/host-id.schema.json"):
                continue
            if LOCAL_HOST_ENUM.search(path.read_text(encoding="utf-8")):
                offenders.append(rel)
    assert offenders == [], f"these surfaces still declare their own host enum: {offenders}"


def test_every_surface_references_the_single_source() -> None:
    for rel in IMPORTING_SURFACES:
        assert "host_identity" in (ROOT / rel).read_text(encoding="utf-8"), rel
    for name in REFERENCING_SCHEMAS:
        schema = json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))
        assert "host-id.schema.json" in json.dumps(schema), name


def test_the_shared_schema_declares_the_modules_own_set_and_rule() -> None:
    defs = json.loads(HOST_ID_SCHEMA.read_text(encoding="utf-8"))["$defs"]
    assert defs["known"]["enum"] == list(KNOWN_HOSTS)
    assert defs["observer"]["enum"] == list(OBSERVER_HOSTS)
    assert defs["external"]["pattern"] == EXTERNAL_HOST_ID_PATTERN
    assert [branch["$ref"] for branch in defs["host"]["oneOf"]] == [
        "#/$defs/known",
        "#/$defs/external",
    ]
    assert [branch["$ref"] for branch in defs["receiptHost"]["oneOf"]] == [
        "#/$defs/known",
        "#/$defs/observer",
        "#/$defs/external",
    ]


def test_the_four_host_bearing_schemas_point_at_the_shared_definition() -> None:
    expected = {
        "profile.schema.json": ("properties", "host"),
        "binding.schema.json": ("properties", "host"),
        "package-descriptor.schema.json": ("properties", "host_targets", "items"),
        "receipt.schema.json": ("properties", "host"),
    }
    for name, node_path in expected.items():
        node = json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))
        for key in node_path:
            node = node[key]
        def_name = "receiptHost" if name == "receipt.schema.json" else "host"
        assert node == {"$ref": f"host-id.schema.json#/$defs/{def_name}"}, name


# --- a declared host validates --------------------------------------------


def test_a_declared_host_is_accepted_by_the_module_and_the_schemas() -> None:
    assert is_valid_host_id(DECLARED)
    assert is_external(DECLARED) and not is_builtin(DECLARED)
    assert _declared_profile().validate() is None

    payload = {
        "host": DECLARED,
        "support_state": "candidate",
        "bindings": [],
        "skills_dir": ".copilot/skills",
        "plugin_manifest": ".copilot-plugin/plugin.json",
    }
    profile_schema = json.loads((SCHEMAS_DIR / "profile.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(profile_schema, registry=_registry()).validate(payload)


def test_two_distinct_declared_hosts_coexist() -> None:
    """Two harnesses from two vendors are two identities, not one `custom`."""
    descriptor = PackageDescriptor(
        id="pstack",
        name="pstack",
        version="1.0.0",
        upstream_pin="0" * 40,
        host_targets=[DECLARED, SECOND_DECLARED],
        skills_root="skills",
        lifecycle={"install": "i", "verify": "v", "uninstall": "u"},
    )
    descriptor.validate()
    for host in (DECLARED, SECOND_DECLARED):
        assert is_valid_host_id(host)
        assert _declared_profile(host).validate() is None

    descriptor_schema = json.loads(
        (SCHEMAS_DIR / "package-descriptor.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(descriptor_schema, registry=_registry()).validate(
        {
            "id": "pstack",
            "name": "pstack",
            "version": "1.0.0",
            "upstream_pin": "0" * 40,
            "host_targets": [DECLARED, SECOND_DECLARED],
            "skills_root": "skills",
            "lifecycle": {"install": "i", "verify": "v", "uninstall": "u"},
        }
    )


def test_a_namespace_collision_is_refused() -> None:
    """A bare new name would collide with the flat built-in namespace."""
    validator = _validator()
    for candidate in ("copilot", "Acme:copilot", "acme:Copilot", "acme:", ":copilot", ""):
        assert not is_valid_host_id(candidate), candidate
        assert not is_external(candidate), candidate
        assert list(validator.iter_errors(candidate)), candidate

    with pytest.raises(ValidationError):
        _declared_profile(host="copilot").validate()
    with pytest.raises(ValidationError):
        PackageDescriptor(
            id="pstack",
            name="pstack",
            version="1.0.0",
            upstream_pin="0" * 40,
            host_targets=["copilot"],
            skills_root="skills",
            lifecycle={"install": "i", "verify": "v", "uninstall": "u"},
        ).validate()

    # A routing table that renames a built-in host is the same collision: the key
    # set is the identity set, so it fails closed instead of routing elsewhere.
    with pytest.raises(HostIdentityError, match="TARGET_MAP"):
        require_builtin_host_keys(
            {**{host: "row" for host in BUILTIN_HOSTS}, "copilot": "row"}, "TARGET_MAP"
        )
    with pytest.raises(HostIdentityError, match="DRIVER_REGISTRY"):
        require_builtin_host_keys({host: "row" for host in BUILTIN_HOSTS[:-1]}, "DRIVER_REGISTRY")


# --- the six built-ins are untouched --------------------------------------


def test_the_six_builtin_hosts_are_unchanged_everywhere() -> None:
    import scripts.portability_schema as portability_schema
    from scripts.drivers import DRIVER_REGISTRY

    lifecycle = _load_module("package_lifecycle_seam", "scripts/package-lifecycle.py")
    verify_portable = _load_module("verify_portable_seam", "scripts/verify-portable.py")
    scan_boundary = _load_module("scan_host_boundary_seam", "scripts/scan-host-boundary.py")
    project_package = _load_module("project_package_seam", "scripts/project-package.py")

    assert BUILTIN_HOSTS == ("grok", "codex", "omp", "opencode", "antigravity", "droid")
    assert portability_schema.HOSTS == KNOWN_HOSTS
    assert verify_portable.SUPPORTED_HOSTS == BUILTIN_HOSTS
    assert lifecycle.SUPPORTED_HOSTS == BUILTIN_HOSTS
    for table in (
        DRIVER_REGISTRY,
        project_package.TARGET_MAP,
        lifecycle.HOST_PLUGIN_REL_PATHS,
        portability_schema.DEFAULT_SKILLS_DIRS,
        portability_schema.DEFAULT_PLUGIN_MANIFESTS,
    ):
        assert set(table) == set(BUILTIN_HOSTS)
    assert scan_boundary.HARNESS_NAMES == set(KNOWN_HOSTS) | set(OBSERVER_HOSTS) | {"pi"}
    assert verify_portable.get_declared_hosts() == [
        "grok",
        "codex",
        "omp",
        "opencode",
        "antigravity",
        "droid",
    ]


def test_the_pre_registry_names_stay_readable() -> None:
    """`claude` and `custom` keep loading; they are aliases, not new identities."""
    assert KNOWN_HOSTS == BUILTIN_HOSTS + LEGACY_HOST_ALIASES
    for alias in LEGACY_HOST_ALIASES:
        assert is_valid_host_id(alias)
        assert not is_external(alias)
    assert is_valid_receipt_host("mock")
    assert _receipt("grok").validate() is None


# --- unknown and unproved stay fail-closed --------------------------------


def test_an_unknown_host_still_fails_closed() -> None:
    from scripts.drivers import get_driver

    for host in ("nope", "", "Grok"):
        with pytest.raises(ValidationError):
            _declared_profile(host=host).validate()
        with pytest.raises(ValidationError):
            _receipt(host).validate()
    with pytest.raises(ValidationError):
        Binding(
            host="nope",
            capability="agent.spawn",
            implementation_status="native",
            enforcement="hard",
            verification_status="unverified",
        ).validate()
    # No silent fallback onto a neighbouring host's driver.
    with pytest.raises(ValueError, match="No native driver registered"):
        get_driver(DECLARED, ROOT)


def test_a_declared_host_cannot_promote_itself() -> None:
    for support_state in ("mapped", "packaged", "verified", "supported"):
        with pytest.raises(ValidationError, match="must stay candidate"):
            _declared_profile(support_state=support_state).validate()

    verified_row = Binding(
        host=DECLARED,
        capability="agent.spawn",
        implementation_status="native",
        enforcement="hard",
        verification_status="verified",
        evidence_ref=".audit/evidence/acme-receipt.json",
    )
    profile = HarnessProfile(
        host=DECLARED,
        support_state="candidate",
        bindings=[verified_row],
        skills_dir=".copilot/skills",
        plugin_manifest=".copilot-plugin/plugin.json",
    )
    with pytest.raises(ValidationError, match="without native evidence"):
        profile.validate()


def test_a_declared_host_receipt_must_name_its_adapter_version() -> None:
    """A candidate host without one stays candidate/GAP: the row cannot read it."""
    with pytest.raises(ValidationError, match="adapter_version"):
        _receipt(DECLARED).validate()
    assert _receipt(DECLARED, adapter_version="acme-adapter 1.2.3").validate() is None
    # The six keep the field optional: no built-in receipt changes shape.
    assert _receipt("grok").validate() is None
    assert _receipt("mock").validate() is None


def test_adapter_version_is_optional_in_the_receipt_schema() -> None:
    schema = json.loads((SCHEMAS_DIR / "receipt.schema.json").read_text(encoding="utf-8"))
    assert "adapter_version" not in schema["required"]
    assert schema["properties"]["adapter_version"]["type"] == "string"
    assert "candidate/GAP" in schema["properties"]["adapter_version"]["description"]


def test_the_receipt_payload_never_serializes_a_null_adapter_version() -> None:
    """The schema types the field as a string, so an unset value is an absent key."""
    verify_portable = _load_module("verify_portable_payload", "scripts/verify-portable.py")
    payload = verify_portable._receipt_payload(_receipt("grok"))
    assert "adapter_version" not in payload
    assert verify_portable._receipt_payload(_receipt(DECLARED, "1.2.3"))["adapter_version"] == "1.2.3"
