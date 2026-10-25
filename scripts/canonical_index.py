#!/usr/bin/env python3
"""Generate, check, and audit canonical pstack inventory and drift from the UPSTREAM pin.

Reads the immutable UPSTREAM pin, discovers canonical principles, playbooks,
and skills, and generates or checks openspec/canonical-inventory.json.
Separates pin_conformance from upstream_freshness.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.surface_revisions import observe_upstream_freshness

UPSTREAM = ROOT / "UPSTREAM"
INVENTORY_FILE = ROOT / "openspec" / "canonical-inventory.json"
DRIFT_FILE = ROOT / "openspec" / "canonical-drift.json"
PIN_RE = re.compile(r"^tree ([0-9a-f]{40})$", re.M)

# Known exclusions with architectural reasons
EXCLUSIONS = {
    ".cursor-plugin/plugin.json": {
        "mode": "exclude",
        "reason": "Cursor-only host manifest",
    },
    "assets/logo.png": {
        "mode": "exclude",
        "reason": "Cursor branding asset",
    },
    ".cursor-plugin": {
        "mode": "exclude",
        "reason": "Cursor-only packaging",
    },
    "skills/make-bot-ui": {
        "mode": "exclude",
        "reason": "Replaced by figure-it-out; excluded per pstack-sync-from-upstream spec",
    },
    "docs/guide/images": {
        "mode": "exclude",
        "reason": "Upstream documentation screenshots; host docs use Markdown tables and plain text",
    },
    "skills/poteto-mode/scripts/check-plan.test.ts": {
        "mode": "exclude",
        "reason": "Cursor-side bun:test twin of the retained check-plan.mjs; the port carries the same fence cases adapted in check-plan.test.mjs",
    },
}

# Known upstream semantic defects with tracked local adaptations (#204, #205)
KNOWN_DEFECT_EXCEPTIONS = {
    "cursor-plugins-474": {
        "surface": "skills/principle-test-behavior-not-implementation/SKILL.md",
        "upstream_issue": "https://github.com/cursor/plugins/issues/474",
        "description": "Upstream principle text conflates vacuous assertions with weak truthiness assertions",
        "reconciliation": "Separated weak assertion fail states from truly vacuous execution-only shapes",
    },
    "cursor-plugins-571": {
        "surface": "skills/principle-exhaust-the-design-space/SKILL.md",
        "upstream_issue": "https://github.com/cursor/plugins/issues/571",
        "description": "Upstream section cut removed the antecedent sentence, leaving the product-design clause orphaned with no governing statement",
        "reconciliation": "Re-anchored the body with the interaction/architectural-decision sentence ahead of the product-design clause",
    }
}

# Known adaptations where host-neutral intent is preserved with host mapping
ADAPTED_PREFIXES = (
    "skills/poteto-mode/SKILL.md",
    "skills/poteto-mode/playbooks/",
    "skills/poteto-mode/scripts/",
    "skills/how/",
    "skills/reflect/",
    "skills/architect/",
    "skills/arena/",
    "skills/interrogate/",
    "skills/figure-it-out/",
    "README.md",
)


def get_pin(root: Path | None = None) -> str:
    active_root = root if root is not None else ROOT
    upstream_file = active_root / "UPSTREAM"
    if not upstream_file.is_file():
        raise SystemExit("UPSTREAM file missing")
    text = upstream_file.read_text(encoding="utf-8")
    m = PIN_RE.search(text)
    if not m:
        raise SystemExit("UPSTREAM missing `tree <40-hex>` line")
    return m.group(1)


def get_git_cache_root(root: Path | None = None) -> Optional[Path]:
    active_root = root if root is not None else ROOT
    proc = subprocess.run(
        ["git", "-C", str(active_root), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        common = Path(proc.stdout.strip())
        if not common.is_absolute():
            common = (active_root / common).resolve()
        else:
            common = common.resolve()
        parent = common.parent if common.name == ".git" else common
        candidate = parent / ".worktrees" / "upstream-cursor-plugins"
        if candidate.is_dir():
            return candidate
    candidate2 = active_root / ".worktrees" / "upstream-cursor-plugins"
    if candidate2.is_dir():
        return candidate2
    return None


def resolve_pstack_tree(cache: Path, pin_sha: str) -> Optional[str]:
    proc = subprocess.run(
        ["git", "-C", str(cache), "ls-tree", pin_sha, "pstack"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 4 and parts[1] == "tree" and parts[3] == "pstack":
            return parts[2]
    return None


def list_tree_artifacts(cache: Path, tree_sha: str) -> List[Dict[str, str]]:
    proc = subprocess.run(
        ["git", "-C", str(cache), "ls-tree", "-r", tree_sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    artifacts = []
    for line in proc.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 4 and parts[1] == "blob":
            artifacts.append({
                "mode_bits": parts[0],
                "hash": parts[2],
                "path": parts[3],
            })
    return artifacts


def classify_artifact(canonical_path: str, blob_hash: str, root: Path | None = None) -> Dict[str, Any]:
    active_root = root if root is not None else ROOT
    # Check explicit exclusions
    for exc_path, info in EXCLUSIONS.items():
        if canonical_path == exc_path or canonical_path.startswith(exc_path + "/"):
            return {
                "path": canonical_path,
                "canonical_hash": blob_hash,
                "category": "excluded",
                "mode": info["mode"],
                "reason": info["reason"],
            }

    # Principles
    if canonical_path.startswith("skills/principle-") and canonical_path.endswith("/SKILL.md"):
        local_file = active_root / canonical_path
        if local_file.is_file():
            return {
                "path": canonical_path,
                "canonical_hash": blob_hash,
                "category": "principle",
                "mode": "preserve",
                "local_path": canonical_path,
            }
        return {
            "path": canonical_path,
            "canonical_hash": blob_hash,
            "category": "principle",
            "mode": "gap",
            "reason": "Missing local principle file",
        }

    # Playbooks
    if canonical_path.startswith("skills/poteto-mode/playbooks/") and canonical_path.endswith(".md"):
        local_file = active_root / canonical_path
        if local_file.is_file():
            return {
                "path": canonical_path,
                "canonical_hash": blob_hash,
                "category": "playbook",
                "mode": "adapt",
                "local_path": canonical_path,
                "reason": "Playbook intent preserved with host-neutral mapping",
            }
        return {
            "path": canonical_path,
            "canonical_hash": blob_hash,
            "category": "playbook",
            "mode": "gap",
            "reason": "Missing local playbook file",
        }

    # General skills & references
    local_file = active_root / canonical_path
    if local_file.is_file():
        is_adapted = any(canonical_path.startswith(prefix) for prefix in ADAPTED_PREFIXES)
        return {
            "path": canonical_path,
            "canonical_hash": blob_hash,
            "category": "skill",
            "mode": "adapt" if is_adapted else "preserve",
            "local_path": canonical_path,
        }

    return {
        "path": canonical_path,
        "canonical_hash": blob_hash,
        "category": "unknown",
        "mode": "gap",
        "reason": "Artifact not mapped or present locally",
    }


def classify_drift_entry(rel_path: str, status: str) -> Dict[str, Any]:
    """Partition upstream changes into Swarm buckets and assess portability impact."""
    if rel_path in EXCLUSIONS or any(rel_path.startswith(k + "/") for k in EXCLUSIONS):
        ex = EXCLUSIONS.get(rel_path) or next(v for k, v in EXCLUSIONS.items() if rel_path.startswith(k + "/"))
        return {
            "path": rel_path,
            "status": status,
            "bucket": "host_cursor" if "cursor" in ex["reason"].lower() else "verification_skills",
            "mode": "exclude",
            "note": ex["reason"],
        }
    if rel_path in (
        "skills/create-formal-verification-skill/SKILL.md",
        "skills/maintain-formal-verification-skill/SKILL.md",
        "skills/in-your-own-words/SKILL.md",
        "skills/sharpen/SKILL.md",
    ):
        return {
            "path": rel_path,
            "status": status,
            "bucket": "verification_skills",
            "mode": "preserve",
            "note": "Source-identical host-neutral leaf skill",
        }
    if rel_path.startswith(".cursor-plugin/") or rel_path == ".cursor-plugin":
        return {
            "path": rel_path,
            "status": status,
            "bucket": "host_cursor",
            "mode": "exclude",
            "note": "Cursor packaging; version bump only",
        }
    if rel_path.startswith("skills/principle-"):
        return {
            "path": rel_path,
            "status": status,
            "bucket": "principles",
            "mode": "preserve",
            "note": "Canonical principle leaf",
        }
    if rel_path.startswith("skills/poteto-mode/playbooks/") or rel_path == "skills/poteto-mode/SKILL.md" or rel_path.startswith("skills/poteto-mode/scripts/"):
        return {
            "path": rel_path,
            "status": status,
            "bucket": "playbooks_router",
            "mode": "adapt",
            "note": "Playbook and router updates; preserved with host-neutral mapping",
        }
    if rel_path.startswith("agents/"):
        return {
            "path": rel_path,
            "status": status,
            "bucket": "agents",
            "mode": "adapt",
            "note": "Role agent definition",
        }
    if rel_path.startswith("docs/") or rel_path == "README.md":
        return {
            "path": rel_path,
            "status": status,
            "bucket": "packaging_docs",
            "mode": "adapt",
            "note": "Documentation guide refresh",
        }
    return {
        "path": rel_path,
        "status": status,
        "bucket": "verification_skills",
        "mode": "adapt",
        "note": "Verification and engineering skill updates",
    }


def classify_drift_report(cache: Path, pin_sha: str, upstream_head: str) -> Dict[str, Any]:
    proc = subprocess.run(
        ["git", "-C", str(cache), "diff", "--name-status", f"{pin_sha}..{upstream_head}", "--", "pstack/"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {"error": "git diff failed", "raw": proc.stderr}

    items = []
    for line in proc.stdout.splitlines():
        parts = line.strip().split("\t", 1)
        if len(parts) == 2:
            status, full_path = parts
            rel = full_path[7:] if full_path.startswith("pstack/") else full_path
            items.append(classify_drift_entry(rel, status))

    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        buckets.setdefault(item["bucket"], []).append(item)

    return {
        "scope": "upstream-pin-to-upstream-HEAD (not local-checkout-vs-upstream)",
        "pin": pin_sha,
        "upstream_head": upstream_head,
        "total_changed_files": len(items),
        "buckets": {k: len(v) for k, v in buckets.items()},
        "entries": items,
    }


def compute_inventory(cache: Optional[Path], root: Path | None = None) -> Dict[str, Any]:
    active_root = root if root is not None else ROOT
    pin_sha = get_pin(active_root)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    inventory_file = active_root / "openspec" / "canonical-inventory.json"

    if cache is None:
        if inventory_file.is_file():
            inv = json.loads(inventory_file.read_text(encoding="utf-8"))
            inv["upstream_freshness"] = "UNKNOWN"
            inv["observation_source"] = None
            inv["observation_time"] = None
            return inv
        raise SystemExit(f"No upstream cache found and {inventory_file} does not exist")

    pstack_tree = resolve_pstack_tree(cache, pin_sha)
    if not pstack_tree:
        raise SystemExit(f"Could not resolve pstack tree under pin {pin_sha}")

    blobs = list_tree_artifacts(cache, pstack_tree)
    classified = [classify_artifact(b["path"], b["hash"], root=active_root) for b in blobs]

    observed = observe_upstream_freshness(active_root, pin_sha, cache)
    upstream_head = observed.upstream_head
    freshness = observed.freshness
    drift_count = observed.commits_ahead

    principles_count = sum(1 for c in classified if c["category"] == "principle" and c["mode"] in ("preserve", "adapt"))
    playbooks_count = sum(1 for c in classified if c["category"] == "playbook" and c["mode"] in ("preserve", "adapt"))
    gaps_count = sum(1 for c in classified if c["mode"] == "gap")

    conformance = "PASS" if gaps_count == 0 else "FAIL"

    inventory = {
        "pin": pin_sha,
        "pstack_tree": pstack_tree,
        "pin_conformance": conformance,
        "upstream_freshness": freshness,
        "upstream_head": upstream_head,
        "observation_time": now_iso,
        "observation_source": str(cache),
        "commits_ahead": drift_count,
        "counts": {
            "principles": principles_count,
            "playbooks": playbooks_count,
            "total_artifacts": len(classified),
            "preserved": sum(1 for c in classified if c["mode"] == "preserve"),
            "adapted": sum(1 for c in classified if c["mode"] == "adapt"),
            "excluded": sum(1 for c in classified if c["mode"] == "exclude"),
            "gaps": gaps_count,
        },
        "known_defect_exceptions": KNOWN_DEFECT_EXCEPTIONS,
        "artifacts": classified,
    }
    return inventory


def main(root: Path | None = None) -> int:
    active_root = root if root is not None else ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true", help="Generate canonical-inventory.json")
    parser.add_argument("--check", action="store_true", help="Check canonical conformance and inventory")
    parser.add_argument("--drift", action="store_true", help="Report upstream drift status")
    parser.add_argument("--classify-drift", action="store_true", help="Generate canonical-drift.json partition classification (scope: upstream-pin-to-upstream-HEAD movement only, not local-checkout-vs-upstream drift)")
    parser.add_argument("--target", help="Explicit target revision to compare against pin (defaults to upstream HEAD)")
    parser.add_argument("--out", type=Path, help="Write the drift report here instead of openspec/canonical-drift.json")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    cache = get_git_cache_root(active_root)
    inventory = compute_inventory(cache, root=active_root)
    inventory_file = active_root / "openspec" / "canonical-inventory.json"
    drift_file = active_root / "openspec" / "canonical-drift.json"

    if args.generate:
        inventory_file.parent.mkdir(parents=True, exist_ok=True)
        inventory_file.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
        print(f"Generated {inventory_file} (pin {inventory['pin'][:7]}, {inventory['counts']['total_artifacts']} artifacts)")
        return 0

    if args.classify_drift:
        if cache is None:
            print("FAIL: Upstream cache not found for drift classification", file=sys.stderr)
            return 1
        target_head = args.target if args.target else inventory["upstream_head"]
        report = classify_drift_report(cache, inventory["pin"], target_head)
        out_file = args.out or drift_file
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Generated {out_file}")
        print(f"Total changed files: {report['total_changed_files']}")
        for bucket, count in report["buckets"].items():
            print(f"  {bucket}: {count}")
        return 0

    if args.json:
        print(json.dumps(inventory, indent=2))
        return 0

    if args.drift:
        print(f"Upstream Freshness: {inventory['upstream_freshness']}")
        print(f"Pin: {inventory['pin']} | Upstream HEAD: {inventory['upstream_head']}")
        print(f"Observation Source: {inventory.get('observation_source')}")
        print(f"Observation Time: {inventory.get('observation_time')}")
        print(f"Commits ahead: {inventory['commits_ahead']}")
        return 0

    # Default is check
    conformance = inventory["pin_conformance"]
    freshness = inventory["upstream_freshness"]
    counts = inventory["counts"]
    print(f"Conformance: {conformance}")
    print(f"Freshness: {freshness} ({inventory['commits_ahead']} commits ahead)")
    print(f"Principles: {counts['principles']} | Playbooks: {counts['playbooks']}")
    print(f"Artifacts: {counts['total_artifacts']} (preserved={counts['preserved']}, adapted={counts['adapted']}, excluded={counts['excluded']}, gaps={counts['gaps']})")

    if conformance != "PASS":
        print("FAIL: Unclassified gaps detected:", file=sys.stderr)
        for art in inventory["artifacts"]:
            if art["mode"] == "gap":
                print(f"  GAP: {art['path']} - {art.get('reason', '')}", file=sys.stderr)
        return 1

    # Validate known defect exceptions
    exceptions = inventory.get("known_defect_exceptions", {})
    for exc_id, exc_data in exceptions.items():
        surf_path = active_root / exc_data["surface"]
        if not surf_path.is_file():
            print(f"FAIL: Defect exception surface missing: {exc_data['surface']}", file=sys.stderr)
            return 1
        issue_id = exc_data["upstream_issue"].rstrip("/").split("/")[-1]
        surf_text = surf_path.read_text(encoding="utf-8")
        if issue_id not in surf_text:
            print(f"FAIL: Defect exception #{issue_id} not referenced in {exc_data['surface']}", file=sys.stderr)
            return 1

    if freshness == "DRIFT":
        print(
            f"UNTESTED: canonical pin {inventory['pin']} is {inventory['commits_ahead']} commits behind "
            f"upstream HEAD {inventory['upstream_head']}; conformance holds for the pin, but its freshness "
            f"is untested until the pin is regenerated.",
        )
        return 2

    print("PASS: Canonical inventory conforms to pin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
