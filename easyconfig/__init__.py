"""Simple configuration management for Python applications."""

from .config import MISSING, Config, ConfigError
from .docs import install_docs

__all__ = ["Config", "ConfigError", "MISSING", "install_docs"]
