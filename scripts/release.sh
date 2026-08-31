#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -n "${__GROK_INSIDE_BWRAP:-}" ]; then
  echo "scripts/release.sh: nested grok cannot write .git/refs/tags. Run from a host shell with grok --sandbox off." >&2
  exit 1
fi
python3 tests/test_release.py
grok plugin validate .
version="$(python3 -c 'import json; print(json.load(open("plugin.json"))["version"])')"
tag="v${version}"
if ! grok --sandbox off plugin tag --push; then
  git rev-parse "refs/tags/${tag}" >/dev/null
  git push origin "refs/tags/${tag}"
fi
if gh release view "$tag" >/dev/null 2>&1; then
  exit 0
fi
gh release create "$tag" --generate-notes --verify-tag
