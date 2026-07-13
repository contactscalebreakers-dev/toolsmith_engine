"""
Snapshot Manager for SB Toolsmith Pro

Manages runtime state persistence, capture, and rollback.
"""

import asyncio
import dataclasses
import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SnapshotMetadata:
    """Snapshot metadata."""
    snapshot_id: str
    tool_key: str
    created_at: datetime
    description: Optional[str] = None
    size_bytes: int = 0
    parent_snapshot_id: Optional[str] = None
    tags: List[str] = dataclasses.field(default_factory=list)


class SnapshotManager:
    """
    Manages runtime snapshots for state persistence and rollback.
    
    Supports:
    - Full snapshots of tool environments
    - Incremental snapshots
    - Snapshot metadata tracking
    - Rollback to previous snapshots
    - Snapshot cleanup and retention policies
    """

    def __init__(self, snapshot_dir: Path):
        """
        Initialize snapshot manager.
        
        Args:
            snapshot_dir: Directory for storing snapshots
        """
        self.snapshot_dir = snapshot_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._metadata: Dict[str, SnapshotMetadata] = {}
        self._lock = asyncio.Lock()

        logger.info(f"SnapshotManager initialized with dir: {snapshot_dir}")

    async def create_snapshot(
        self,
        tool_key: str,
        source_path: Path,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Create a snapshot of a tool environment.
        
        Args:
            tool_key: Tool identifier
            source_path: Path to environment to snapshot
            description: Optional description
            tags: Optional tags
            
        Returns:
            Snapshot ID
        """
        snapshot_id = str(uuid.uuid4())
        snapshot_path = self.snapshot_dir / tool_key / snapshot_id

        try:
            logger.info(f"Creating snapshot {snapshot_id} for {tool_key}")

            # Create snapshot directory
            snapshot_path.mkdir(parents=True, exist_ok=True)

            # Copy environment
            if source_path.exists():
                for item in source_path.iterdir():
                    if item.is_dir():
                        shutil.copytree(
                            item,
                            snapshot_path / item.name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                        )
                    else:
                        shutil.copy2(item, snapshot_path / item.name)

            # Calculate size
            size_bytes = sum(
                f.stat().st_size
                for f in snapshot_path.rglob("*")
                if f.is_file()
            )

            # Create metadata
            metadata = SnapshotMetadata(
                snapshot_id=snapshot_id,
                tool_key=tool_key,
                created_at=datetime.utcnow(),
                description=description,
                size_bytes=size_bytes,
                tags=tags or [],
            )

            async with self._lock:
                self._metadata[snapshot_id] = metadata

            logger.info(
                f"Snapshot {snapshot_id} created successfully "
                f"({size_bytes} bytes)"
            )

            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}", exc_info=True)
            if snapshot_path.exists():
                shutil.rmtree(snapshot_path)
            raise

    async def restore_snapshot(
        self,
        snapshot_id: str,
        target_path: Path,
    ) -> bool:
        """
        Restore a snapshot to target location.
        
        Args:
            snapshot_id: Snapshot ID to restore
            target_path: Target path for restoration
            
        Returns:
            True if successful
        """
        async with self._lock:
            metadata = self._metadata.get(snapshot_id)

        if not metadata:
            logger.warning(f"Snapshot not found: {snapshot_id}")
            return False

        snapshot_path = self.snapshot_dir / metadata.tool_key / snapshot_id

        if not snapshot_path.exists():
            logger.error(f"Snapshot data not found: {snapshot_path}")
            return False

        try:
            logger.info(f"Restoring snapshot {snapshot_id} to {target_path}")

            # Remove existing target
            if target_path.exists():
                shutil.rmtree(target_path)

            # Copy snapshot to target
            shutil.copytree(snapshot_path, target_path)

            logger.info(f"Snapshot {snapshot_id} restored successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to restore snapshot: {e}", exc_info=True)
            return False

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: Snapshot ID to delete
            
        Returns:
            True if deleted
        """
        async with self._lock:
            metadata = self._metadata.get(snapshot_id)

        if not metadata:
            return False

        snapshot_path = self.snapshot_dir / metadata.tool_key / snapshot_id

        try:
            if snapshot_path.exists():
                shutil.rmtree(snapshot_path)
                logger.info(f"Deleted snapshot {snapshot_id}")

            async with self._lock:
                del self._metadata[snapshot_id]

            return True

        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}", exc_info=True)
            return False

    async def get_metadata(self, snapshot_id: str) -> Optional[SnapshotMetadata]:
        """Get snapshot metadata."""
        async with self._lock:
            return self._metadata.get(snapshot_id)

    async def list_snapshots(self, tool_key: Optional[str] = None) -> List[SnapshotMetadata]:
        """
        List snapshots.
        
        Args:
            tool_key: Optional tool filter
            
        Returns:
            List of snapshot metadata
        """
        async with self._lock:
            if tool_key:
                return [
                    m for m in self._metadata.values()
                    if m.tool_key == tool_key
                ]
            return list(self._metadata.values())

    async def get_latest_snapshot(self, tool_key: str) -> Optional[SnapshotMetadata]:
        """Get latest snapshot for tool."""
        snapshots = await self.list_snapshots(tool_key)
        if not snapshots:
            return None
        return max(snapshots, key=lambda m: m.created_at)

    async def cleanup_old_snapshots(
        self,
        tool_key: str,
        keep_count: int = 5,
    ) -> int:
        """
        Clean up old snapshots, keeping most recent.
        
        Args:
            tool_key: Tool identifier
            keep_count: Number of snapshots to keep
            
        Returns:
            Number of snapshots deleted
        """
        snapshots = await self.list_snapshots(tool_key)
        if len(snapshots) <= keep_count:
            return 0

        # Sort by creation time, keep most recent
        sorted_snapshots = sorted(
            snapshots,
            key=lambda m: m.created_at,
            reverse=True,
        )

        deleted_count = 0
        for snapshot in sorted_snapshots[keep_count:]:
            if await self.delete_snapshot(snapshot.snapshot_id):
                deleted_count += 1

        logger.info(
            f"Cleaned up {deleted_count} snapshots for {tool_key}, "
            f"keeping {keep_count}"
        )

        return deleted_count

    async def export_snapshot(
        self,
        snapshot_id: str,
        export_path: Path,
    ) -> bool:
        """
        Export snapshot to archive.
        
        Args:
            snapshot_id: Snapshot ID to export
            export_path: Path for export archive
            
        Returns:
            True if successful
        """
        async with self._lock:
            metadata = self._metadata.get(snapshot_id)

        if not metadata:
            return False

        snapshot_path = self.snapshot_dir / metadata.tool_key / snapshot_id

        try:
            logger.info(f"Exporting snapshot {snapshot_id} to {export_path}")

            # Create archive
            archive_path = shutil.make_archive(
                str(export_path.with_suffix("")),
                "zip",
                snapshot_path,
            )

            logger.info(f"Snapshot exported to {archive_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export snapshot: {e}", exc_info=True)
            return False

    async def import_snapshot(
        self,
        tool_key: str,
        archive_path: Path,
        description: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import snapshot from archive.
        
        Args:
            tool_key: Tool identifier
            archive_path: Path to archive
            description: Optional description
            
        Returns:
            Snapshot ID if successful
        """
        snapshot_id = str(uuid.uuid4())
        snapshot_path = self.snapshot_dir / tool_key / snapshot_id

        try:
            logger.info(f"Importing snapshot from {archive_path}")

            # Create snapshot directory
            snapshot_path.mkdir(parents=True, exist_ok=True)

            # Extract archive
            shutil.unpack_archive(str(archive_path), snapshot_path)

            # Calculate size
            size_bytes = sum(
                f.stat().st_size
                for f in snapshot_path.rglob("*")
                if f.is_file()
            )

            # Create metadata
            metadata = SnapshotMetadata(
                snapshot_id=snapshot_id,
                tool_key=tool_key,
                created_at=datetime.utcnow(),
                description=description,
                size_bytes=size_bytes,
            )

            async with self._lock:
                self._metadata[snapshot_id] = metadata

            logger.info(f"Snapshot imported successfully: {snapshot_id}")
            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to import snapshot: {e}", exc_info=True)
            if snapshot_path.exists():
                shutil.rmtree(snapshot_path)
            return None

    async def get_statistics(self) -> Dict[str, Any]:
        """Get snapshot statistics."""
        async with self._lock:
            total_size = sum(m.size_bytes for m in self._metadata.values())
            by_tool = {}
            for metadata in self._metadata.values():
                if metadata.tool_key not in by_tool:
                    by_tool[metadata.tool_key] = {
                        "count": 0,
                        "size_bytes": 0,
                    }
                by_tool[metadata.tool_key]["count"] += 1
                by_tool[metadata.tool_key]["size_bytes"] += metadata.size_bytes

            return {
                "total_snapshots": len(self._metadata),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "by_tool": by_tool,
            }
