#!/usr/bin/env python3
"""Generate, check, and audit canonical pstack inventory and drift from the UPSTREAM pin.

Reads the immutable UPSTREAM pin, discovers canonical principles, playbooks,
and skills, and generates or checks openspec/canonical-inventory.json.
Separates pin_conformance from upstream_freshness.

Usage:
    python3 scripts/canonical-index.py --check
    python3 scripts/canonical-index.py --generate
    python3 scripts/canonical-index.py --drift
    python3 scripts/canonical-index.py --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "UPSTREAM"
INVENTORY_FILE = ROOT / "openspec" / "canonical-inventory.json"
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
    "HARNESS.md",
    "README.md",
)


def get_pin() -> str:
    if not UPSTREAM.is_file():
        raise SystemExit("UPSTREAM file missing")
    text = UPSTREAM.read_text(encoding="utf-8")
    m = PIN_RE.search(text)
    if not m:
        raise SystemExit("UPSTREAM missing `tree <40-hex>` line")
    return m.group(1)


def get_git_cache_root() -> Optional[Path]:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        common = Path(proc.stdout.strip())
        if not common.is_absolute():
            common = (ROOT / common).resolve()
        else:
            common = common.resolve()
        parent = common.parent if common.name == ".git" else common
        candidate = parent / ".worktrees" / "upstream-cursor-plugins"
        if candidate.is_dir():
            return candidate
    candidate2 = ROOT / ".worktrees" / "upstream-cursor-plugins"
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


def classify_artifact(canonical_path: str, blob_hash: str) -> Dict[str, Any]:
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
        local_file = ROOT / canonical_path
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
        local_file = ROOT / canonical_path
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
    local_file = ROOT / canonical_path
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


def compute_inventory(cache: Optional[Path]) -> Dict[str, Any]:
    pin_sha = get_pin()
    if cache is None:
        if INVENTORY_FILE.is_file():
            return json.loads(INVENTORY_FILE.read_text(encoding="utf-8"))
        raise SystemExit("No upstream cache found and openspec/canonical-inventory.json does not exist")

    pstack_tree = resolve_pstack_tree(cache, pin_sha)
    if not pstack_tree:
        raise SystemExit(f"Could not resolve pstack tree under pin {pin_sha}")

    blobs = list_tree_artifacts(cache, pstack_tree)
    classified = [classify_artifact(b["path"], b["hash"]) for b in blobs]

    # Check upstream head for drift
    head_proc = subprocess.run(
        ["git", "-C", str(cache), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    upstream_head = head_proc.stdout.strip() if head_proc.returncode == 0 else "unknown"

    drift_proc = subprocess.run(
        ["git", "-C", str(cache), "rev-list", f"{pin_sha}..HEAD", "--count"],
        capture_output=True,
        text=True,
        check=False,
    )
    drift_count = int(drift_proc.stdout.strip()) if drift_proc.returncode == 0 and drift_proc.stdout.strip().isdigit() else 0

    principles_count = sum(1 for c in classified if c["category"] == "principle" and c["mode"] in ("preserve", "adapt"))
    playbooks_count = sum(1 for c in classified if c["category"] == "playbook" and c["mode"] in ("preserve", "adapt"))
    gaps_count = sum(1 for c in classified if c["mode"] == "gap")

    conformance = "PASS" if gaps_count == 0 else "FAIL"
    freshness = "DRIFT" if drift_count > 0 else "CURRENT"

    inventory = {
        "pin": pin_sha,
        "pstack_tree": pstack_tree,
        "pin_conformance": conformance,
        "upstream_freshness": freshness,
        "upstream_head": upstream_head,
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
        "artifacts": classified,
    }
    return inventory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true", help="Generate canonical-inventory.json")
    parser.add_argument("--check", action="store_true", help="Check canonical conformance and inventory")
    parser.add_argument("--drift", action="store_true", help="Report upstream drift status")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    cache = get_git_cache_root()
    inventory = compute_inventory(cache)

    if args.generate:
        INVENTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        INVENTORY_FILE.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
        print(f"Generated {INVENTORY_FILE} (pin {inventory['pin'][:7]}, {inventory['counts']['total_artifacts']} artifacts)")
        sys.exit(0)

    if args.json:
        print(json.dumps(inventory, indent=2))
        sys.exit(0)

    if args.drift:
        print(f"Upstream Freshness: {inventory['upstream_freshness']}")
        print(f"Pin: {inventory['pin']} | Upstream HEAD: {inventory['upstream_head']}")
        print(f"Commits ahead: {inventory['commits_ahead']}")
        sys.exit(0)

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
        sys.exit(1)

    print("PASS: Canonical inventory conforms to pin.")
    sys.exit(0)


if __name__ == "__main__":
    main()
