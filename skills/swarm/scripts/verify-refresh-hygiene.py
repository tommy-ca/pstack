#!/usr/bin/env python3
"""Thin entrypoint facade forwarding to verify_refresh_hygiene.py."""

from pathlib import Path
import runpy
import sys

TARGET = Path(__file__).resolve().with_name("verify_refresh_hygiene.py")

if __name__ == "__main__":
    runpy.run_path(str(TARGET), run_name="__main__")
