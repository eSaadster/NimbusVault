from pathlib import Path
from typing import Optional

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
        """Return a unique file path by adding a numeric suffix if needed."""
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
        """Save the given content to disk and return the saved file path."""

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

        with open(file_path, "wb") as f:
            f.write(content)

        return str(file_path)

