"""Level library — scan and delete saved levels (stdlib only)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LevelEntry:
    """Metadata for a single saved level file."""

    name: str
    path: Path
    modified_at: float


class LevelLibrary:
    """Static helpers to browse and manage the level folder."""

    @staticmethod
    def scan(folder: str | os.PathLike[str] = "data/levels") -> list[LevelEntry]:
        """Return *LevelEntry* objects for every ``.json`` in *folder*, newest first.

        Returns an empty list when the folder does not exist.
        """
        folder = Path(folder)
        if not folder.is_dir():
            return []

        entries: list[LevelEntry] = []
        for f in folder.glob("*.json"):
            try:
                mtime = f.stat().st_mtime
            except FileNotFoundError:
                continue
            
            entries.append(
                LevelEntry(
                    name=f.stem,
                    path=f,
                    modified_at=mtime,
                )
            )

        entries.sort(key=lambda e: e.modified_at, reverse=True)
        return entries

    @staticmethod
    def delete(entry: LevelEntry) -> None:
        """Remove the level file from disk. No-op if already absent."""
        entry.path.unlink(missing_ok=True)
