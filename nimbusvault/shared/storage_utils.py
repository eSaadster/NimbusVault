from pathlib import Path
from typing import Optional, Dict, Union

# --------------------------
# In-Memory File Persistence
# --------------------------

_MEMORY_STORE: Dict[str, bytes] = {}


def save_file(file_path: str, data: bytes, use_disk: bool = True) -> str:
    """Persist data to file_path using disk or memory store."""
    if use_disk:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as fh:
            fh.write(data)
    else:
        _MEMORY_STORE[file_path] = data
    return file_path


def load_file(file_path: str, use_disk: bool = True) -> Optional[bytes]:
    """Load data from file_path using disk or memory store."""
    if use_disk:
        path = Path(file_path)
        if not path.exists():
            return None
        return path.read_bytes()
    return _MEMORY_STORE.get(file_path)


# --------------------------
# Vault-Aware File Organizer
# --------------------------

class VaultStorage:
    """Utility class to organize and save files in the vault storage."""

    def __init__(self) -> None:
        self.root = Path("/vault-storage")
        self.uploads = self.root / "uploads"
        self.files = self.root / "files"
        self.users = self.root / "users"
        self.shared = self.root / "shared"
        self.trash = self.root / "trash"

    def _sanitize_filename(self, name: str) -> str:
        """Remove potentially unsafe characters from a filename."""
        allowed = set("-_. ")
        return "".join(c for c in name if c.isalnum() or c in allowed)

    def _get_unique_path(self, base: Path) -> Path:
        """Ensure a unique file path by adding a numeric suffix if needed."""
        if not base.exists():
            return base
        stem = base.stem
        suffix = base.suffix
        counter = 1
        while True:
            candidate = base.with_name(f"{stem}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def save_file(
        self,
        content: bytes,
        filename: str,
        user_id: Optional[str] = None,
        storage_type: str = "files",
    ) -> str:
        """Save content to appropriate vault directory and return file path."""
        if storage_type == "user" and user_id:
            target_dir = self.users / user_id
        elif storage_type == "shared":
            target_dir = self.shared
        elif storage_type == "uploads":
            target_dir = self.uploads
        elif storage_type == "trash":
            target_dir = self.trash
        else:
            target_dir = self.files

        target_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = self._sanitize_filename(filename)
        file_path = self._get_unique_path(target_dir / safe_filename)

        with file_path.open("wb") as f:
            f.write(content)

        return str(file_path)
