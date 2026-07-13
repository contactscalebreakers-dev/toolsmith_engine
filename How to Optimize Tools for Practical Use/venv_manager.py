"""
Virtual Environment Manager for SB Toolsmith Pro

Create, manage, and cleanup virtual environments.
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class VirtualEnvironment:
    """Represents a virtual environment."""

    def __init__(self, path: Path):
        """
        Initialize virtual environment.
        
        Args:
            path: Path to venv
        """
        self.path = path
        self.python_executable = self._get_python_executable()
        self.pip_executable = self._get_pip_executable()

    def _get_python_executable(self) -> Path:
        """Get Python executable path."""
        if sys.platform == "win32":
            return self.path / "Scripts" / "python.exe"
        else:
            return self.path / "bin" / "python"

    def _get_pip_executable(self) -> Path:
        """Get pip executable path."""
        if sys.platform == "win32":
            return self.path / "Scripts" / "pip.exe"
        else:
            return self.path / "bin" / "pip"

    def is_valid(self) -> bool:
        """Check if venv is valid."""
        return self.python_executable.exists() and self.pip_executable.exists()

    def get_python_version(self) -> Optional[str]:
        """Get Python version in venv."""
        try:
            result = subprocess.run(
                [str(self.python_executable), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except:
            return None

    async def get_installed_packages(self) -> Dict[str, str]:
        """Get installed packages."""
        try:
            result = await asyncio.create_subprocess_exec(
                str(self.pip_executable),
                "list",
                "--format=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await result.communicate()
            packages = json.loads(stdout.decode())

            return {pkg["name"]: pkg["version"] for pkg in packages}

        except Exception as e:
            logger.error(f"Failed to get installed packages: {e}")
            return {}

    async def install_requirements(
        self,
        requirements: List[str],
        backend: str = "pip",
    ) -> Tuple[bool, str]:
        """
        Install requirements.
        
        Args:
            requirements: List of package specs
            backend: Package manager (pip, poetry, uv)
            
        Returns:
            (success, output)
        """
        try:
            if backend == "poetry":
                return await self._install_with_poetry(requirements)
            elif backend == "uv":
                return await self._install_with_uv(requirements)
            else:
                return await self._install_with_pip(requirements)

        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False, str(e)

    async def _install_with_pip(
        self,
        requirements: List[str],
    ) -> Tuple[bool, str]:
        """Install with pip."""
        cmd = [str(self.pip_executable), "install", "--upgrade"] + requirements

        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await result.communicate()
        output = stdout.decode() + stderr.decode()

        return result.returncode == 0, output

    async def _install_with_poetry(
        self,
        requirements: List[str],
    ) -> Tuple[bool, str]:
        """Install with poetry."""
        # Poetry requires pyproject.toml
        cmd = ["poetry", "add"] + requirements

        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await result.communicate()
        output = stdout.decode() + stderr.decode()

        return result.returncode == 0, output

    async def _install_with_uv(
        self,
        requirements: List[str],
    ) -> Tuple[bool, str]:
        """Install with uv."""
        cmd = ["uv", "pip", "install"] + requirements

        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**dict(os.environ), "VIRTUAL_ENV": str(self.path)},
        )

        stdout, stderr = await result.communicate()
        output = stdout.decode() + stderr.decode()

        return result.returncode == 0, output

    def get_stats(self) -> Dict[str, Any]:
        """Get venv statistics."""
        return {
            "path": str(self.path),
            "valid": self.is_valid(),
            "python_version": self.get_python_version(),
            "python_executable": str(self.python_executable),
            "pip_executable": str(self.pip_executable),
        }


class VirtualEnvironmentManager:
    """Manage virtual environments."""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize venv manager.
        
        Args:
            base_dir: Base directory for venvs
        """
        self.base_dir = base_dir or Path.home() / ".sb-toolsmith" / "venvs"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._venvs: Dict[str, VirtualEnvironment] = {}

    async def create_venv(
        self,
        venv_id: str,
        python_version: Optional[str] = None,
    ) -> Optional[VirtualEnvironment]:
        """
        Create a new virtual environment.
        
        Args:
            venv_id: Unique venv identifier
            python_version: Python version (optional)
            
        Returns:
            VirtualEnvironment or None
        """
        try:
            venv_path = self.base_dir / venv_id

            # Create venv
            cmd = [sys.executable, "-m", "venv", str(venv_path)]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.error(f"Failed to create venv: {stderr.decode()}")
                return None

            venv = VirtualEnvironment(venv_path)

            if not venv.is_valid():
                logger.error(f"Created venv is invalid: {venv_path}")
                return None

            self._venvs[venv_id] = venv
            logger.info(f"Virtual environment created: {venv_id}")

            return venv

        except Exception as e:
            logger.error(f"Venv creation failed: {e}")
            return None

    async def get_venv(self, venv_id: str) -> Optional[VirtualEnvironment]:
        """Get existing venv."""
        if venv_id in self._venvs:
            return self._venvs[venv_id]

        # Try to load from disk
        venv_path = self.base_dir / venv_id
        if venv_path.exists():
            venv = VirtualEnvironment(venv_path)
            if venv.is_valid():
                self._venvs[venv_id] = venv
                return venv

        return None

    async def delete_venv(self, venv_id: str) -> bool:
        """Delete virtual environment."""
        try:
            venv_path = self.base_dir / venv_id

            if venv_path.exists():
                import shutil
                shutil.rmtree(venv_path)

            if venv_id in self._venvs:
                del self._venvs[venv_id]

            logger.info(f"Virtual environment deleted: {venv_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete venv: {e}")
            return False

    async def cleanup_all(self) -> None:
        """Clean up all venvs."""
        for venv_id in list(self._venvs.keys()):
            await self.delete_venv(venv_id)

    def list_venvs(self) -> List[str]:
        """List all venvs."""
        return list(self._venvs.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_venvs": len(self._venvs),
            "base_dir": str(self.base_dir),
            "venvs": {
                vid: venv.get_stats()
                for vid, venv in self._venvs.items()
            },
        }


import os
