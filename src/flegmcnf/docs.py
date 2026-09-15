from __future__ import annotations

import argparse
import importlib.metadata
import sys
from pathlib import Path
from shutil import copy2


DOC_FILES = ("README.md", "Syntax.md")
REPOSITORY_URL = "https://github.com/Third-Flegm/EasyCoFlegmCNF"
QUICKSTART_FILE = "docs/QUICKSTART.md"


def _documentation_path(file_name: str) -> Path:
    """Locate documentation in a source checkout or installed distribution."""
    source_path = Path(__file__).resolve().parents[2] / "docs" / file_name
    if source_path.exists():
        return source_path
    return Path(sys.prefix) / "flegmcnf-docs" / file_name


def install_docs(target_dir: str | Path | None = None, *, force: bool = False) -> list[Path]:
    """Copy the packaged docs into a target directory and return the copied paths."""
    target = Path(target_dir) if target_dir is not None else Path.cwd()
    target.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for file_name in DOC_FILES:
        source = _documentation_path(file_name)
        destination = target / file_name
        if not source.exists():
            continue
        if destination.exists() and not force:
            continue
        if destination.exists() and force:
            try:
                destination.unlink()
            except OSError:
                continue
        copy2(source, destination)
        copied.append(destination)
    return copied


def install_quickstart(target_dir: str | Path | None = None, *, force: bool = False) -> Path | None:
    """Copy the bundled quick-start guide into a target directory."""
    target = Path(target_dir) if target_dir is not None else Path.cwd()
    target.mkdir(parents=True, exist_ok=True)
    destination = target / QUICKSTART_FILE
    if destination.exists() and not force:
        return None
    try:
        source = _documentation_path("docs/Quickstart.md")
        if not source.exists():
            return None
        copy2(source, destination)
    except OSError:
        return None
    return destination


def _install_docs_to_site_packages() -> int:
    """CLI entry point for documentation and project helper commands."""
    parser = argparse.ArgumentParser(
        prog="flegmcnf",
        description="Install FlegmCNF documentation and show project information.",
        epilog="With no action, README.md and Syntax.md are copied to the target directory.",
    )
    parser.add_argument("target", nargs="?", default=".", help="Directory to receive the docs files.")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--quickstart",
        action="store_true",
        help="Write QUICKSTART.md to the target directory.",
    )
    actions.add_argument(
        "--repo",
        action="store_true",
        help="Print the FlegmCNF GitHub repository URL.",
    )
    actions.add_argument(
        "--version",
        action="version",
        version=f"flegmcnf {importlib.metadata.version('FlegmCNF')}",
        help="Show the installed FlegmCNF version.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing README.md and Syntax.md files in the target directory.",
    )
    args = parser.parse_args()
    if args.repo:
        print(REPOSITORY_URL)
    elif args.quickstart:
        install_quickstart(args.target, force=args.force)
    else:
        install_docs(args.target, force=args.force)
    return 0
