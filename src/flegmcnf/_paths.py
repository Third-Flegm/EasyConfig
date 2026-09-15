from __future__ import annotations

import inspect
import os
import tempfile
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent


def path_from_caller(path: str | os.PathLike[str]) -> Path:
    """Resolve a relative path from the first non-library caller frame."""
    file_path = Path(path)
    if file_path.is_absolute():
        return file_path

    frame = inspect.currentframe()
    try:
        caller = frame
        while caller is not None:
            caller_name = caller.f_code.co_filename
            if caller_name and not caller_name.startswith("<"):
                candidate = Path(caller_name).resolve()
                if not candidate.is_relative_to(PACKAGE_DIR):
                    return candidate.parent / file_path
            caller = caller.f_back
    finally:
        del frame

    return file_path


def atomic_write(file_path: Path, content: str) -> None:
    """Write text atomically to avoid partial output on interruption."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=file_path.parent, delete=False
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, file_path)
    except OSError:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
