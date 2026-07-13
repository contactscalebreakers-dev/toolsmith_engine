"""
Plugin Manifest System for SB Toolsmith Pro

Defines plugin capabilities, permissions, and sandbox boundaries.
"""

import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class Capability(Enum):
    """Plugin capabilities."""
    RUNTIME_EXECUTE = "runtime.execute"
    GRAPH_NODE = "graph.node"
    TERMINAL_STREAM = "terminal.stream"
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    NETWORK_HTTP = "network.http"
    PROCESS_SPAWN = "process.spawn"
    PLUGIN_LOAD = "plugin.load"
    EVENT_SUBSCRIBE = "event.subscribe"
    AGENT_CALL = "agent.call"


class PermissionScope(Enum):
    """Permission scopes."""
    WORKSPACE = "workspace"
    SYSTEM = "system"
    NETWORK = "network"
    UNRESTRICTED = "unrestricted"


@dataclass
class PermissionModel:
    """Plugin permission model."""
    filesystem: List[str] = None  # Allowed paths
    network: bool = False
    subprocess: bool = False
    environment_vars: List[str] = None  # Allowed env vars
    max_memory_mb: int = 512
    max_cpu_percent: int = 100
    max_runtime_seconds: int = 3600

    def __post_init__(self):
        if self.filesystem is None:
            self.filesystem = []
        if self.environment_vars is None:
            self.environment_vars = []


@dataclass
class PluginManifest:
    """Plugin manifest definition."""
    id: str
    name: str
    version: str
    entry: str
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    capabilities: List[str] = None
    permissions: Optional[PermissionModel] = None
    dependencies: List[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.dependencies is None:
            self.dependencies = []
        if self.permissions is None:
            self.permissions = PermissionModel()
        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate manifest.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.id:
            return False, "Plugin ID is required"
        if not self.name:
            return False, "Plugin name is required"
        if not self.version:
            return False, "Plugin version is required"
        if not self.entry:
            return False, "Plugin entry point is required"

        # Validate capabilities
        valid_capabilities = {c.value for c in Capability}
        for cap in self.capabilities:
            if cap not in valid_capabilities:
                return False, f"Invalid capability: {cap}"

        # Validate version format (semantic versioning)
        parts = self.version.split(".")
        if len(parts) != 3:
            return False, "Version must be semantic (major.minor.patch)"

        return True, None

    def has_capability(self, capability: str) -> bool:
        """Check if plugin has capability."""
        return capability in self.capabilities

    def can_access_filesystem(self, path: str) -> bool:
        """Check if plugin can access filesystem path."""
        if not self.permissions:
            return False

        for allowed_path in self.permissions.filesystem:
            if path.startswith(allowed_path):
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "entry": self.entry,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "capabilities": self.capabilities,
            "permissions": asdict(self.permissions) if self.permissions else None,
            "dependencies": self.dependencies,
            "config_schema": self.config_schema,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        """Create from dictionary."""
        permissions_data = data.get("permissions")
        permissions = (
            PermissionModel(**permissions_data)
            if permissions_data
            else PermissionModel()
        )

        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            entry=data["entry"],
            description=data.get("description"),
            author=data.get("author"),
            license=data.get("license"),
            capabilities=data.get("capabilities", []),
            permissions=permissions,
            dependencies=data.get("dependencies", []),
            config_schema=data.get("config_schema"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json_file(cls, path: Path) -> "PluginManifest":
        """Load from JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data)

    def to_json_file(self, path: Path) -> None:
        """Save to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class ManifestValidator:
    """Validates plugin manifests."""

    @staticmethod
    def validate_manifest(manifest: PluginManifest) -> tuple[bool, Optional[str]]:
        """
        Validate manifest comprehensively.
        
        Args:
            manifest: Manifest to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation
        is_valid, error = manifest.validate()
        if not is_valid:
            return False, error

        # Validate permissions
        if manifest.permissions:
            if manifest.permissions.max_memory_mb < 1:
                return False, "max_memory_mb must be >= 1"
            if manifest.permissions.max_cpu_percent < 1 or manifest.permissions.max_cpu_percent > 100:
                return False, "max_cpu_percent must be between 1 and 100"
            if manifest.permissions.max_runtime_seconds < 1:
                return False, "max_runtime_seconds must be >= 1"

        # Validate config schema if present
        if manifest.config_schema:
            if not isinstance(manifest.config_schema, dict):
                return False, "config_schema must be a dictionary"

        return True, None

    @staticmethod
    def validate_entry_point(manifest: PluginManifest, plugin_dir: Path) -> tuple[bool, Optional[str]]:
        """
        Validate plugin entry point exists.
        
        Args:
            manifest: Manifest to validate
            plugin_dir: Plugin directory
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        entry_path = plugin_dir / manifest.entry
        if not entry_path.exists():
            return False, f"Entry point not found: {manifest.entry}"

        if not entry_path.is_file():
            return False, f"Entry point is not a file: {manifest.entry}"

        return True, None


class ManifestRegistry:
    """Registry of loaded plugin manifests."""

    def __init__(self):
        """Initialize registry."""
        self._manifests: Dict[str, PluginManifest] = {}
        self._lock = asyncio.Lock()

    async def register(self, manifest: PluginManifest) -> bool:
        """
        Register a manifest.
        
        Args:
            manifest: Manifest to register
            
        Returns:
            True if registered
        """
        is_valid, error = ManifestValidator.validate_manifest(manifest)
        if not is_valid:
            logger.error(f"Invalid manifest {manifest.id}: {error}")
            return False

        async with self._lock:
            self._manifests[manifest.id] = manifest

        logger.info(f"Registered plugin manifest: {manifest.id}")
        return True

    async def unregister(self, plugin_id: str) -> bool:
        """Unregister a manifest."""
        async with self._lock:
            if plugin_id in self._manifests:
                del self._manifests[plugin_id]
                logger.info(f"Unregistered plugin manifest: {plugin_id}")
                return True
        return False

    async def get(self, plugin_id: str) -> Optional[PluginManifest]:
        """Get manifest by ID."""
        async with self._lock:
            return self._manifests.get(plugin_id)

    async def get_all(self) -> Dict[str, PluginManifest]:
        """Get all manifests."""
        async with self._lock:
            return self._manifests.copy()

    async def get_by_capability(self, capability: str) -> List[PluginManifest]:
        """Get all manifests with capability."""
        async with self._lock:
            return [
                m for m in self._manifests.values()
                if m.has_capability(capability)
            ]


# Import asyncio at module level
import asyncio
