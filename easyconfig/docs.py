from __future__ import annotations

from pathlib import Path
from shutil import copy2


DOC_FILES = ("README.md", "Syntax.md")


def install_docs(target_dir: str | Path | None = None) -> list[Path]:
    """Copy the packaged docs into a target directory and return the copied paths."""
    target = Path(target_dir) if target_dir is not None else Path.cwd()
    target.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for file_name in DOC_FILES:
        source = Path(__file__).resolve().parent.parent / file_name
        destination = target / file_name
        if source.exists():
            copy2(source, destination)
            copied.append(destination)
    return copied


def _install_docs_to_site_packages() -> None:
    """Helper for a CLI entry point to place the docs next to installed package files."""
    package_root = Path(__file__).resolve().parent
    install_docs(package_root.parent)
