"""Deprecated alias for the AndroidLife harness package.

Prefer ``import androidlife`` / ``from androidlife import ...``.
This shim keeps ``from DailyBench...`` working during the rename window.
"""
from androidlife import *  # noqa: F403

__all__ = getattr(__import__("androidlife"), "__all__", [])
