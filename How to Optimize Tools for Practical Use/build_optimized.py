#!/usr/bin/env python3
"""
Optimized Build Script for SB Toolsmith Pro

Builds standalone Windows executable with optimization and packaging.
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class OptimizedBuilder:
    """Build SB Toolsmith Pro with optimization."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize builder."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.setup_logging()

    def setup_logging(self) -> None:
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def clean(self) -> bool:
        """Clean previous builds."""
        logger.info("Cleaning previous builds...")
        try:
            for directory in [self.dist_dir, self.build_dir]:
                if directory.exists():
                    shutil.rmtree(directory)
                    logger.info(f"Removed {directory}")
            return True
        except Exception as e:
            logger.error(f"Clean failed: {e}")
            return False

    def optimize_code(self) -> bool:
        """Optimize Python code."""
        logger.info("Optimizing Python code...")
        try:
            # Compile Python files to bytecode
            import py_compile

            for py_file in self.project_root.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    try:
                        py_compile.compile(str(py_file), doraise=True)
                        logger.debug(f"Compiled {py_file}")
                    except py_compile.PyCompileError as e:
                        logger.warning(f"Compilation warning: {e}")

            logger.info("Code optimization complete")
            return True

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return False

    def build_exe(self, onefile: bool = True) -> bool:
        """Build executable with PyInstaller."""
        logger.info("Building executable...")

        try:
            # PyInstaller arguments
            args = [
                sys.executable,
                "-m",
                "PyInstaller",
                "--name=SBToolsmithPro",
                "--windowed",
                "--distpath=" + str(self.dist_dir),
                "--buildpath=" + str(self.build_dir),
                "--specpath=" + str(self.project_root / "scripts"),
                "--add-data=" + str(self.project_root / "config") + ":config",
                "--add-data=" + str(self.project_root / "utils") + ":utils",
                "--hidden-import=PySide6",
                "--hidden-import=PySide6.QtCore",
                "--hidden-import=PySide6.QtGui",
                "--hidden-import=PySide6.QtWidgets",
                "--hidden-import=asyncio",
                "--hidden-import=aiohttp",
                "--collect-all=PySide6",
                "--strip",
                "--noupx",
                "--noconfirm",
            ]

            if onefile:
                args.insert(3, "--onefile")
            else:
                args.insert(3, "--onedir")

            # Add icon if exists
            icon_path = self.project_root / "assets" / "icon.ico"
            if icon_path.exists():
                args.append(f"--icon={icon_path}")

            args.append(str(self.project_root / "main_integrated.py"))

            logger.info(f"Running PyInstaller...")
            result = subprocess.run(args, cwd=str(self.project_root))

            if result.returncode == 0:
                self._print_build_stats()
                return True
            else:
                logger.error(f"PyInstaller failed with code {result.returncode}")
                return False

        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False

    def _print_build_stats(self) -> None:
        """Print build statistics."""
        exe_path = self.dist_dir / "SBToolsmithPro" / "SBToolsmithPro.exe"

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Executable: {exe_path}")
            logger.info(f"✓ Size: {size_mb:.2f} MB")
        else:
            exe_path = self.dist_dir / "SBToolsmithPro.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                logger.info(f"✓ Executable: {exe_path}")
                logger.info(f"✓ Size: {size_mb:.2f} MB")

    def create_installer(self) -> bool:
        """Create Windows installer."""
        logger.info("Creating Windows installer...")

        try:
            nsis_path = Path("C:/Program Files (x86)/NSIS/makensis.exe")

            if not nsis_path.exists():
                logger.warning("NSIS not found. Skipping installer creation.")
                return False

            # Generate NSIS script
            nsis_script = self._generate_nsis_script()
            script_path = self.project_root / "scripts" / "installer.nsi"

            with open(script_path, "w") as f:
                f.write(nsis_script)

            logger.info(f"Generated NSIS script: {script_path}")

            # Run NSIS
            result = subprocess.run([str(nsis_path), str(script_path)])

            if result.returncode == 0:
                logger.info("✓ Installer created successfully")
                return True
            else:
                logger.error(f"NSIS failed with code {result.returncode}")
                return False

        except Exception as e:
            logger.error(f"Installer creation failed: {e}")
            return False

    def _generate_nsis_script(self) -> str:
        """Generate NSIS installer script."""
        return r"""
; SB Toolsmith Pro Installer

!include "MUI2.nsh"
!include "x64.nsh"

Name "SB Toolsmith Pro"
OutFile "SBToolsmithPro-1.0.0-setup.exe"
InstallDir "$PROGRAMFILES64\SBToolsmithPro"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "dist\SBToolsmithPro\*.*"
  
  CreateDirectory "$SMPROGRAMS\SBToolsmithPro"
  CreateShortCut "$SMPROGRAMS\SBToolsmithPro\SB Toolsmith Pro.lnk" "$INSTDIR\SBToolsmithPro.exe"
  CreateShortCut "$SMPROGRAMS\SBToolsmithPro\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  CreateShortCut "$DESKTOP\SB Toolsmith Pro.lnk" "$INSTDIR\SBToolsmithPro.exe"
  
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SBToolsmithPro" "DisplayName" "SB Toolsmith Pro"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SBToolsmithPro" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\SBToolsmithPro"
  Delete "$DESKTOP\SB Toolsmith Pro.lnk"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SBToolsmithPro"
SectionEnd
"""

    def create_deployment_package(self) -> bool:
        """Create deployment package."""
        logger.info("Creating deployment package...")

        try:
            package_dir = self.project_root / "deployment"
            package_dir.mkdir(exist_ok=True)

            # Copy executable
            exe_src = self.dist_dir / "SBToolsmithPro" / "SBToolsmithPro.exe"
            if not exe_src.exists():
                exe_src = self.dist_dir / "SBToolsmithPro.exe"

            if exe_src.exists():
                shutil.copy2(exe_src, package_dir / "SBToolsmithPro.exe")
                logger.info(f"Copied executable to {package_dir}")

            # Copy documentation
            for doc in ["README.md", "ARCHITECTURE.md", "PHASE_8_INTEGRATION.md"]:
                src = self.project_root / doc
                if src.exists():
                    shutil.copy2(src, package_dir / doc)

            logger.info(f"✓ Deployment package created: {package_dir}")
            return True

        except Exception as e:
            logger.error(f"Package creation failed: {e}")
            return False

    def get_build_info(self) -> dict:
        """Get build information."""
        info = {
            "project_root": str(self.project_root),
            "dist_dir": str(self.dist_dir),
            "build_dir": str(self.build_dir),
            "dist_exists": self.dist_dir.exists(),
            "build_exists": self.build_dir.exists(),
        }

        # Find executable
        for exe_path in [
            self.dist_dir / "SBToolsmithPro" / "SBToolsmithPro.exe",
            self.dist_dir / "SBToolsmithPro.exe",
        ]:
            if exe_path.exists():
                info["exe_path"] = str(exe_path)
                info["exe_size_mb"] = exe_path.stat().st_size / (1024 * 1024)
                break

        return info


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Build SB Toolsmith Pro")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--optimize", action="store_true", help="Optimize code")
    parser.add_argument("--onefile", action="store_true", help="Build single file")
    parser.add_argument("--installer", action="store_true", help="Create installer")
    parser.add_argument("--package", action="store_true", help="Create deployment package")

    args = parser.parse_args()

    builder = OptimizedBuilder()

    print("=" * 70)
    print("SB Toolsmith Pro - Optimized Build")
    print("=" * 70)

    if args.clean:
        if not builder.clean():
            return 1

    if args.optimize:
        if not builder.optimize_code():
            return 1

    if not builder.build_exe(onefile=args.onefile):
        return 1

    if args.installer:
        if not builder.create_installer():
            logger.warning("Installer creation skipped")

    if args.package:
        if not builder.create_deployment_package():
            return 1

    # Print info
    print("\n" + "=" * 70)
    print("Build Information:")
    print("=" * 70)
    for key, value in builder.get_build_info().items():
        print(f"{key}: {value}")

    print("=" * 70)
    print("Build complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
