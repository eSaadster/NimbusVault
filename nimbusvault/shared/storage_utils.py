"""Utility helpers for saving and loading files."""

from pathlib import Path
from typing import Dict

_MEMORY_STORE: Dict[str, bytes] = {}


def save_file(file_path: str, data: bytes, use_disk: bool = True) -> str:
    """Persist ``data`` to ``file_path``.

    When ``use_disk`` is ``True`` the contents are written to disk.  Otherwise
    the contents are kept in an in-memory dictionary which acts as a very
    lightweight persistence layer for development and testing.
    """

    if use_disk:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as fh:
            fh.write(data)
    else:
        _MEMORY_STORE[file_path] = data

    return file_path


def load_file(file_path: str, use_disk: bool = True) -> bytes | None:
    """Retrieve file contents previously saved with :func:`save_file`."""

    if use_disk:
        path = Path(file_path)
        if not path.exists():
            return None
        return path.read_bytes()

    return _MEMORY_STORE.get(file_path)
