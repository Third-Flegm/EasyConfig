"""Backward-compatible entrypoint for the modular config implementation."""

import os

from .config import MISSING, Config, ConfigError

__all__ = ["Config", "ConfigError", "MISSING", "os"]
