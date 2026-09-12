"""Path-safe tar extraction for downloaded model runtimes."""

from __future__ import annotations

from pathlib import Path
import tarfile


def _validated_members(archive: tarfile.TarFile, destination: Path) -> list[tarfile.TarInfo]:
    root = destination.resolve()
    valid: list[tarfile.TarInfo] = []
    for member in archive.getmembers():
        # Symlinks and hardlinks can escape the destination even when the
        # apparent member name is safe, so the runtime archive rejects them.
        if member.issym() or member.islnk():
            raise ValueError(f"Links are not permitted in runtime archives: {member.name}")
        candidate = (root / member.name).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Archive member escapes destination: {member.name}") from exc
        valid.append(member)
    return valid


def safe_extract_tar(archive_path: str | Path, destination: str | Path) -> list[Path]:
    """Extract regular tar members after rejecting traversal and links."""

    archive_path = Path(archive_path)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:*") as archive:
        members = _validated_members(archive, destination)
        archive.extractall(destination, members=members)
    return [destination / member.name for member in members]
