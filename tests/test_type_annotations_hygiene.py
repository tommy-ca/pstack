#!/usr/bin/env python3
"""Regression test for type annotations hygiene across scripts and drivers (#761, #764).

Asserts that typing.get_type_hints evaluates cleanly on all callables and classes
without latent NameError exceptions caused by missing typing imports.
"""

from __future__ import annotations

import importlib
import os
import sys
import typing
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_all_scripts_and_drivers_pass_type_hints_evaluation() -> None:
    errors: list[str] = []
    scripts_dir = ROOT / "scripts"
    py_files: list[Path] = sorted(
        list(scripts_dir.glob("*.py")) + list((scripts_dir / "drivers").glob("*.py"))
    )

    for path in py_files:
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(ROOT)
        modname = str(rel).replace(".py", "").replace(os.sep, ".")
        try:
            mod = importlib.import_module(modname)
        except Exception as err:
            errors.append(f"{modname} failed import: {err}")
            continue

        for attr_name in dir(mod):
            if attr_name.startswith("__") and attr_name.endswith("__"):
                continue
            try:
                attr = getattr(mod, attr_name)
            except Exception:
                continue

            if callable(attr) and hasattr(attr, "__annotations__") and attr.__annotations__:
                try:
                    typing.get_type_hints(attr)
                except NameError as err:
                    errors.append(f"{modname}.{attr_name}: NameError: {err}")

    assert not errors, "Latent typing NameError found in scripts/drivers:\n" + "\n".join(errors)
