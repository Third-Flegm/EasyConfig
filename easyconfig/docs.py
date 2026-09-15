from __future__ import annotations

import argparse
import sys
from pathlib import Path
from shutil import copy2


DOC_FILES = ("README.md", "Syntax.md")


def install_docs(target_dir: str | Path | None = None, *, force: bool = False) -> list[Path]:
    """Copy the packaged docs into a target directory and return the copied paths."""
    target = Path(target_dir) if target_dir is not None else Path.cwd()
    target.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for file_name in DOC_FILES:
        source = Path(__file__).resolve().parent.parent / file_name
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


def _install_docs_to_site_packages() -> int:
    """CLI entry point. Defaults to the current working directory and accepts an optional target path."""
    parser = argparse.ArgumentParser(description="Copy the bundled README and Syntax docs into a folder.")
    parser.add_argument("target", nargs="?", default=".", help="Directory to receive the docs files.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing README.md and Syntax.md files in the target directory.",
    )
    args = parser.parse_args()
    install_docs(args.target, force=args.force)
    return 0
