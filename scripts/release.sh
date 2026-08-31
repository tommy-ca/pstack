#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tests/test_release.py
grok plugin validate .
grok plugin tag --push
