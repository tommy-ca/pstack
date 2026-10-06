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

DRIVER_REGISTRY: Dict[str, Type[HarnessDriver]] = {
    "grok": GrokDriver,
    "antigravity": AntigravityDriver,
    "codex": CodexDriver,
    "omp": OMPDriver,
    "opencode": OpenCodeDriver,
    "droid": DroidDriver,
}


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
