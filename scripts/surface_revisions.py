"""AST docstring stripping, disk-backed cache in ~/.cache/pstack, and surface revision computation.

Separated from portability_schema.py for modular decomposition (#593).
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
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

SKILLS_HASH_IGNORED_DIRS = frozenset({"__pycache__", "node_modules"})
SKILLS_HASH_IGNORED_SUFFIXES = (".pyc", ".pyo")


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
    upstream_freshness: str = "UNKNOWN"
    commits_ahead: int = -1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UpstreamFreshness:
    upstream_head: str
    freshness: str
    commits_ahead: int


def _upstream_cache(root: Path) -> Optional[Path]:
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        common = Path(proc.stdout.strip())
        common = common.resolve() if common.is_absolute() else (root / common).resolve()
        parent = common.parent if common.name == ".git" else common
        candidate = parent / ".worktrees" / "upstream-cursor-plugins"
        if candidate.is_dir():
            return candidate
    fallback = root / ".worktrees" / "upstream-cursor-plugins"
    return fallback if fallback.is_dir() else None


def observe_upstream_freshness(
    root: Path, pin: str, cache: Optional[Path] = None
) -> UpstreamFreshness:
    """Observe how far the upstream cache HEAD has moved past the pin."""
    cache = cache or _upstream_cache(root)
    if cache is None:
        return UpstreamFreshness("unknown", "UNKNOWN", -1)
    head = subprocess.run(
        ["git", "-C", str(cache), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if head.returncode != 0:
        return UpstreamFreshness("unknown", "UNKNOWN", -1)
    upstream_head = head.stdout.strip()
    drift = subprocess.run(
        ["git", "-C", str(cache), "rev-list", f"{pin}..HEAD", "--count"],
        capture_output=True,
        text=True,
        check=False,
    )
    if drift.returncode != 0 or not drift.stdout.strip().isdigit():
        return UpstreamFreshness(upstream_head, "UNKNOWN", -1)
    commits_ahead = int(drift.stdout.strip())
    return UpstreamFreshness(
        upstream_head, "DRIFT" if commits_ahead else "CURRENT", commits_ahead
    )


class RecipeError(RuntimeError):
    """The driver-fingerprint recipe refused to produce a revision (fail closed)."""


DOCSTRING_CONSUMED_DRIVERS = (
    "canonical-index.py",
    "verify-portable.py",
    "portable_verifier.py",
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


_DRIVER_CORE_CACHE_VERSION = 1
_DRIVER_CORE_CACHE_MAX_RECORDS = 256
_DRIVER_CORE_CACHE_MAX_BYTES = 32 * 1024 * 1024


def _driver_core_cache_dir() -> Optional[Path]:
    if os.name != "posix":
        return None
    raw_cache_home = os.environ.get("XDG_CACHE_HOME")
    try:
        base = Path(raw_cache_home).expanduser() if raw_cache_home else Path.home() / ".cache"
        if not base.is_absolute():
            return None
        cache_dir = Path(os.path.abspath(base / "pstack" / "driver-core"))
        current = Path(cache_dir.anchor)
        owner_uid = os.geteuid()

        for component in cache_dir.parts[1:]:
            current /= component
            current.mkdir(mode=0o700, exist_ok=True)
            info = current.lstat()
            if not stat.S_ISDIR(info.st_mode):
                return None
            if info.st_uid not in (0, owner_uid):
                return None
            if info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX:
                return None
            if current == cache_dir:
                if info.st_uid != owner_uid:
                    return None
                if info.st_mode & 0o077:
                    current.chmod(0o700)
                    info = current.lstat()
                if info.st_uid != owner_uid or info.st_mode & 0o077:
                    return None
        return cache_dir
    except (OSError, RuntimeError, ValueError):
        return None


def _read_driver_core_cache(
    cache_file: Path, expected: Dict[str, Any]
) -> Optional[bytes]:
    try:
        info = cache_file.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > _DRIVER_CORE_CACHE_MAX_BYTES:
            return None
        if os.name == "posix" and (
            info.st_uid != os.getuid() or info.st_mode & 0o077
        ):
            return None
        record = json.loads(cache_file.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or any(
            record.get(name) != value for name, value in expected.items()
        ):
            return None
        encoded = record.get("core_b64")
        if not isinstance(encoded, str):
            return None
        core = base64.b64decode(encoded, validate=True)
        if record.get("core_sha256") != hashlib.sha256(core).hexdigest():
            return None
        return core
    except (OSError, ValueError, TypeError, binascii.Error, RecursionError):
        return None


def _prune_driver_core_cache(cache_dir: Path) -> None:
    try:
        entries = []
        for path in cache_dir.iterdir():
            is_record = path.suffix == ".json"
            is_temp = path.name.startswith(".driver-core-") and path.name.endswith(".tmp")
            if not is_record and not is_temp:
                continue
            try:
                info = path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode):
                entries.append(
                    (info.st_mtime_ns, path.name, path, is_record, info.st_size)
                )

        record_count = sum(entry[3] for entry in entries)
        total_bytes = sum(entry[4] for entry in entries)
        max_records = _DRIVER_CORE_CACHE_MAX_RECORDS
        max_bytes = _DRIVER_CORE_CACHE_MAX_BYTES
        for _, _, path, is_record, size in sorted(entries):
            if (
                record_count <= max_records
                and total_bytes <= max_bytes
            ):
                break
            try:
                path.unlink()
            except OSError:
                continue
            total_bytes -= size
            if is_record:
                record_count -= 1
    except OSError:
        pass


def _write_driver_core_cache(
    cache_dir: Path, cache_file: Path, record: Dict[str, Any]
) -> None:
    temporary: Optional[Path] = None
    try:
        payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(payload) > _DRIVER_CORE_CACHE_MAX_BYTES:
            return
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".driver-core-",
            suffix=".tmp",
            dir=cache_dir,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
        os.replace(temporary, cache_file)
    except (OSError, UnicodeError, ValueError, TypeError):
        return
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
    _prune_driver_core_cache(cache_dir)


_DRIVER_CORE_MEMO: Dict[Tuple[str, bytes], bytes] = {}


def _driver_core(path: Path, src: bytes) -> bytes:
    key = (path.name, src)
    core = _DRIVER_CORE_MEMO.get(key)
    if core is not None:
        return core

    cache_dir = _driver_core_cache_dir()
    cache_file: Optional[Path] = None
    cache_metadata: Dict[str, Any] = {}
    if cache_dir is not None:
        python_tag = sys.implementation.cache_tag or ""
        source_sha256 = hashlib.sha256(src).hexdigest()
        cache_metadata = {
            "format": _DRIVER_CORE_CACHE_VERSION,
            "python_tag": python_tag,
            "basename": path.name,
            "source_size": len(src),
            "source_sha256": source_sha256,
        }
        cache_key = hashlib.sha256(
            b"\0".join(
                (
                    f"driver-core-v{_DRIVER_CORE_CACHE_VERSION}".encode("ascii"),
                    python_tag.encode("utf-8"),
                    path.name.encode("utf-8", "surrogatepass"),
                    source_sha256.encode("ascii"),
                )
            )
        ).hexdigest()
        cache_file = cache_dir / f"{cache_key}.json"
        core = _read_driver_core_cache(cache_file, cache_metadata)
        if core is not None:
            _DRIVER_CORE_MEMO[key] = core
            return core

    try:
        tree = ast.parse(src.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError) as err:
        raise RecipeError(f"unparseable driver {path}: {err}") from err
    published = _module_docstring(tree) if path.name in DOCSTRING_CONSUMED_DRIVERS else b""
    core = ast.unparse(_strip_docstrings(tree)).encode("utf-8") + published
    _DRIVER_CORE_MEMO[key] = core
    if cache_dir is not None and cache_file is not None:
        record = {
            **cache_metadata,
            "core_b64": base64.b64encode(core).decode("ascii"),
            "core_sha256": hashlib.sha256(core).hexdigest(),
        }
        _write_driver_core_cache(cache_dir, cache_file, record)
    return core


def _update_driver_digest(hasher: Any, path: Path) -> None:
    """Fold `path` into `hasher` as its behaviour-bearing core.

    The core is `ast.unparse` of the parsed module with docstrings stripped, so a
    comment, docstring, blank line or reformat cannot move a revision — only an
    edit the AST can carry does (#444). A file that will not parse raises
    `RecipeError` rather than silently degrading to a whole-file byte hash, and
    a `DOCSTRING_CONSUMED_DRIVERS` module contributes its published module
    docstring raw because the core would drop it.
    """
    hasher.update(_driver_core(path, path.read_bytes()))


def compute_surface_revisions(root: Path, host: str, profile_path: Optional[Path] = None) -> SurfaceRevisions:
    upstream_file = root / "UPSTREAM"
    canonical_pin = "unknown"
    if upstream_file.is_file():
        m = re.search(r"^tree ([0-9a-f]{40})$", upstream_file.read_text(encoding="utf-8"), re.M)
        if m:
            canonical_pin = m.group(1)

    inv_file = root / "openspec" / "canonical-inventory.json"
    upstream_head = "unknown"
    if inv_file.is_file():
        try:
            inv = json.loads(inv_file.read_text(encoding="utf-8"))
            upstream_head = inv.get("upstream_head", "unknown")
        except Exception:
            pass

    observed = observe_upstream_freshness(root, canonical_pin)
    if observed.upstream_head != "unknown":
        upstream_head = observed.upstream_head

    spec_file = root / "openspec" / "specs" / "pstack-portability" / "spec.md"
    spec_hash = hashlib.sha256(spec_file.read_bytes()).hexdigest() if spec_file.is_file() else "missing"

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
                        category = type(err.__cause__).__name__ if err.__cause__ else type(err).__name__
                        hasher.update(f"recipe-error:{category}:".encode("utf-8"))
                        hasher.update(hashlib.sha256(p.read_bytes()).digest())
                else:
                    hasher.update(p.read_bytes())
        skills_tree_hash = hasher.hexdigest()
    else:
        skills_tree_hash = "missing"

    if profile_path is None:
        profile_path = root / "profiles" / f"{host}.json"
        if not profile_path.is_file() and ":" in host:
            alt_path = root / "profiles" / f"{host.split(':')[-1]}.json"
            if alt_path.is_file():
                profile_path = alt_path
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

    manifest_rel = None
    if profile_path.is_file():
        try:
            pdata = json.loads(profile_path.read_text(encoding="utf-8"))
            if pdata.get("plugin_manifest"):
                manifest_rel = pdata["plugin_manifest"]
        except Exception:
            pass
    if manifest_rel is None:
        from scripts.portability_types import DEFAULT_PLUGIN_MANIFESTS

        manifest_rel = DEFAULT_PLUGIN_MANIFESTS.get(host)
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

    hasher = hashlib.sha256()
    for fname in (
        "canonical-index.py",
        "verify-portable.py",
        "portable_verifier.py",
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

    pkg_hasher = hashlib.sha256()
    for fname in (
        "project-package.py",
        "package_projection.py",
        "package-lifecycle.py",
        "package_lifecycle.py",
        "sync-antigravity-plugin.py",
        "model_role_policy.py",
        "model_role_resolver.py",
        "portability_types.py",
        "portability_schema.py",
    ):
        p = root / "scripts" / fname
        if p.is_file():
            pkg_hasher.update(fname.encode("utf-8"))
            _update_driver_digest(pkg_hasher, p)
    policy_file = root / "examples" / "portability" / "model-role-policy.example.json"
    if policy_file.is_file():
        pkg_hasher.update(b"model-role-policy.example.json")
        pkg_hasher.update(policy_file.read_bytes())
    else:
        pkg_hasher.update(b"model-role-policy.example.json:missing")
    schema_file = root / "schemas" / "portability" / "model-role-policy.schema.json"
    if schema_file.is_file():
        pkg_hasher.update(b"model-role-policy.schema.json")
        pkg_hasher.update(schema_file.read_bytes())
    else:
        pkg_hasher.update(b"model-role-policy.schema.json:missing")
    package_driver_revision = pkg_hasher.hexdigest()

    bnd_hasher = hashlib.sha256()
    for fname in ("scan-host-boundary.py", "scan_host_boundary.py"):
        bnd_driver_file = root / "scripts" / fname
        if bnd_driver_file.is_file():
            bnd_hasher.update(fname.encode("utf-8"))
            _update_driver_digest(bnd_hasher, bnd_driver_file)
    boundary_driver_revision = bnd_hasher.hexdigest()

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
        upstream_freshness=observed.freshness,
        commits_ahead=observed.commits_ahead,
    )
