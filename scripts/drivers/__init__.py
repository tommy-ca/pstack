#!/usr/bin/env python3
"""Host-native harness drivers factory and exports."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Type

from .antigravity import AntigravityDriver
from .base import DriverScenarioResult, HarnessDriver
from .codex import CodexDriver
from .droid import DroidDriver
from .grok import GrokDriver
from .omp import OMPDriver
from .opencode import OpenCodeDriver

from scripts.host_identity import require_builtin_host_keys

DRIVER_REGISTRY: Dict[str, Type[HarnessDriver]] = {
    "grok": GrokDriver,
    "antigravity": AntigravityDriver,
    "codex": CodexDriver,
    "omp": OMPDriver,
    "opencode": OpenCodeDriver,
    "droid": DroidDriver,
}

# Every built-in host has exactly one native driver, and no host outside the
# built-in set can be driven: the registry routes, host_identity decides who
# exists (#446). `get_driver` refuses anything else instead of falling back to a
# neighbouring host's driver.
require_builtin_host_keys(DRIVER_REGISTRY, "DRIVER_REGISTRY")


def get_driver(host: str, root: Path) -> HarnessDriver:
    """Instantiate and return the host-native driver for the given harness."""
    driver_cls = DRIVER_REGISTRY.get(host)
    if not driver_cls:
        raise ValueError(f"No native driver registered for host '{host}'. Supported: {list(DRIVER_REGISTRY.keys())}")
    return driver_cls(root)


__all__ = [
    "HarnessDriver",
    "DriverScenarioResult",
    "get_driver",
    "GrokDriver",
    "AntigravityDriver",
    "CodexDriver",
    "OMPDriver",
    "OpenCodeDriver",
    "DroidDriver",
]
