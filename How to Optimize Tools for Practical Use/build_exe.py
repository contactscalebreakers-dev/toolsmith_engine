"""
Build Script for SB Toolsmith Pro Windows Executable

Uses PyInstaller to create standalone .exe with all dependencies.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def build_exe():
    """Build standalone Windows executable."""
    
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # PyInstaller command
    pyinstaller_args = [
        "pyinstaller",
        "--name=SBToolsmithPro",
        "--onefile",
        "--windowed",
        "--icon=resources/icon.ico",
        "--add-data=resources:resources",
        "--add-data=plugins:plugins",
        "--hidden-import=PySide6",
        "--hidden-import=asyncio",
        "--hidden-import=sqlalchemy",
        "--hidden-import=pydantic",
        "--collect-all=PySide6",
        str(project_root / "main.py"),
    ]
    
    print("Building SB Toolsmith Pro executable...")
    print(f"Command: {' '.join(pyinstaller_args)}")
    
    result = subprocess.run(pyinstaller_args, cwd=str(project_root))
    
    if result.returncode == 0:
        exe_path = dist_dir / "SBToolsmithPro.exe"
        print(f"\n✓ Build successful!")
        print(f"✓ Executable: {exe_path}")
        print(f"✓ Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        return 0
    else:
        print("\n✗ Build failed!")
        return 1


def create_installer():
    """Create Windows installer with NSIS."""
    
    project_root = Path(__file__).parent.parent
    nsis_script = project_root / "scripts" / "installer.nsi"
    
    if not nsis_script.exists():
        print(f"NSIS script not found: {nsis_script}")
        return 1
    
    print("\nCreating Windows installer...")
    
    result = subprocess.run(
        ["makensis", str(nsis_script)],
        cwd=str(project_root)
    )
    
    if result.returncode == 0:
        print("✓ Installer created successfully!")
        return 0
    else:
        print("✗ Installer creation failed!")
        return 1


def main():
    """Main build function."""
    
    print("=" * 60)
    print("SB Toolsmith Pro - Build Script")
    print("=" * 60)
    
    # Build executable
    exe_result = build_exe()
    
    if exe_result != 0:
        return exe_result
    
    # Optionally create installer
    if len(sys.argv) > 1 and sys.argv[1] == "--installer":
        installer_result = create_installer()
        if installer_result != 0:
            return installer_result
    
    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
