"""
DependencyAgent for SB Toolsmith Pro

Analyzes dependencies and resolves conflicts.
"""

import asyncio
import ast
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .base_agent import Agent, AgentAction, AgentDecision, AgentExecutionResult, AgentStatus

logger = logging.getLogger(__name__)


class DependencyAgent(Agent):
    """
    Dependency Agent - Analyzes and resolves dependencies.
    
    Responsibilities:
    - Parse Python source code for imports
    - Detect dependency requirements
    - Identify version conflicts
    - Suggest compatible versions
    - Build dependency graphs
    - Optimize package selection
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: Optional[Any] = None,
        runtime_manager: Optional[Any] = None,
    ):
        """Initialize dependency agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type="dependency",
            event_bus=event_bus,
            runtime_manager=runtime_manager,
        )

    async def execute(self, context: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute dependency analysis.
        
        Args:
            context: Execution context containing:
                - source_path: Path to source code
                - requirements_file: Path to requirements file
                - installed_packages: Currently installed packages
                
        Returns:
            Execution result with dependency analysis
        """
        start_time = datetime.utcnow()
        execution_id = context.get("execution_id", "unknown")

        try:
            self.status = AgentStatus.RUNNING

            source_path = context.get("source_path")
            requirements_file = context.get("requirements_file")
            installed_packages = context.get("installed_packages", {})

            logger.info(f"DependencyAgent analyzing dependencies")

            # Extract dependencies from source
            inferred_deps = await self._infer_dependencies_from_source(source_path)
            logger.info(f"Inferred {len(inferred_deps)} dependencies from source")

            # Parse requirements file
            declared_deps = await self._parse_requirements_file(requirements_file)
            logger.info(f"Found {len(declared_deps)} declared dependencies")

            # Detect conflicts
            conflicts = await self._detect_conflicts(
                inferred_deps,
                declared_deps,
                installed_packages,
            )
            logger.info(f"Detected {len(conflicts)} conflicts")

            # Suggest resolutions
            resolutions = await self._suggest_resolutions(conflicts)

            if conflicts:
                decision = await self.record_decision(
                    AgentDecision.PROCEED,
                    f"Detected {len(conflicts)} conflicts, proposing resolutions",
                    confidence=0.85,
                    alternatives=[r["strategy"] for r in resolutions],
                )
                status = AgentStatus.COMPLETED
            else:
                decision = await self.record_decision(
                    AgentDecision.SKIP,
                    "No dependency conflicts detected",
                    confidence=0.95,
                )
                status = AgentStatus.COMPLETED

            # Propose action
            action = AgentAction(
                action_type="resolve_dependencies",
                description="Resolve dependency conflicts",
                parameters={
                    "inferred_dependencies": list(inferred_deps.keys()),
                    "declared_dependencies": list(declared_deps.keys()),
                    "conflicts": len(conflicts),
                    "resolutions": resolutions,
                },
                priority=1,
                reversible=True,
            )
            await self.propose_action(action)

            duration = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_id=self.agent_id,
                execution_id=execution_id,
                status=status,
                actions=[action],
                decisions=[decision],
                result={
                    "inferred_dependencies": inferred_deps,
                    "declared_dependencies": declared_deps,
                    "conflicts": conflicts,
                    "resolutions": resolutions,
                },
                duration_seconds=duration,
            )

            self.status = status
            await self._record_execution(result)

            return result

        except Exception as e:
            logger.error(f"DependencyAgent failed: {e}", exc_info=True)
            duration = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_id=self.agent_id,
                execution_id=execution_id,
                status=AgentStatus.FAILED,
                error=str(e),
                duration_seconds=duration,
            )

            self.status = AgentStatus.FAILED
            await self._record_execution(result)

            return result

    async def _infer_dependencies_from_source(
        self,
        source_path: Optional[str],
    ) -> Dict[str, str]:
        """
        Infer dependencies from Python source code.
        
        Args:
            source_path: Path to source code
            
        Returns:
            Dict of inferred dependencies
        """
        dependencies = {}

        if not source_path:
            return dependencies

        try:
            path = Path(source_path)
            if path.is_file():
                # Single file
                deps = await self._extract_imports_from_file(path)
                dependencies.update(deps)
            elif path.is_dir():
                # Directory of Python files
                for py_file in path.rglob("*.py"):
                    deps = await self._extract_imports_from_file(py_file)
                    dependencies.update(deps)

        except Exception as e:
            logger.warning(f"Failed to infer dependencies: {e}")

        return dependencies

    async def _extract_imports_from_file(self, file_path: Path) -> Dict[str, str]:
        """Extract imports from Python file."""
        imports = {}

        try:
            with open(file_path) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split(".")[0]
                        imports[module] = "*"  # Unknown version
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split(".")[0]
                        imports[module] = "*"

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")

        return imports

    async def _parse_requirements_file(
        self,
        requirements_file: Optional[str],
    ) -> Dict[str, str]:
        """
        Parse requirements file.
        
        Args:
            requirements_file: Path to requirements file
            
        Returns:
            Dict of package -> version
        """
        requirements = {}

        if not requirements_file:
            return requirements

        try:
            path = Path(requirements_file)
            if path.exists():
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Parse requirement
                            match = re.match(r"^([a-zA-Z0-9\-_]+)(.*)$", line)
                            if match:
                                package = match.group(1)
                                version = match.group(2).strip() or "*"
                                requirements[package] = version

        except Exception as e:
            logger.warning(f"Failed to parse requirements: {e}")

        return requirements

    async def _detect_conflicts(
        self,
        inferred: Dict[str, str],
        declared: Dict[str, str],
        installed: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """
        Detect dependency conflicts.
        
        Args:
            inferred: Inferred dependencies
            declared: Declared dependencies
            installed: Installed packages
            
        Returns:
            List of conflicts
        """
        conflicts = []

        # Check for missing declared dependencies
        for package, version in declared.items():
            if package not in inferred and package not in installed:
                conflicts.append({
                    "type": "unused_dependency",
                    "package": package,
                    "declared_version": version,
                })

        # Check for missing inferred dependencies
        for package, version in inferred.items():
            if package not in declared and package not in installed:
                conflicts.append({
                    "type": "missing_dependency",
                    "package": package,
                    "inferred_version": version,
                })

        # Check for version conflicts
        for package in set(inferred.keys()) & set(declared.keys()):
            if inferred[package] != "*" and declared[package] != "*":
                if inferred[package] != declared[package]:
                    conflicts.append({
                        "type": "version_conflict",
                        "package": package,
                        "inferred_version": inferred[package],
                        "declared_version": declared[package],
                    })

        return conflicts

    async def _suggest_resolutions(
        self,
        conflicts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Suggest conflict resolutions.
        
        Args:
            conflicts: List of conflicts
            
        Returns:
            List of suggested resolutions
        """
        resolutions = []

        for conflict in conflicts:
            conflict_type = conflict.get("type")

            if conflict_type == "unused_dependency":
                resolutions.append({
                    "conflict": conflict,
                    "strategy": "remove_unused",
                    "description": f"Remove unused dependency: {conflict['package']}",
                    "action": "remove_from_requirements",
                })

            elif conflict_type == "missing_dependency":
                resolutions.append({
                    "conflict": conflict,
                    "strategy": "add_missing",
                    "description": f"Add missing dependency: {conflict['package']}",
                    "action": "add_to_requirements",
                })

            elif conflict_type == "version_conflict":
                resolutions.append({
                    "conflict": conflict,
                    "strategy": "resolve_version",
                    "description": (
                        f"Resolve version conflict for {conflict['package']}: "
                        f"{conflict['inferred_version']} vs {conflict['declared_version']}"
                    ),
                    "action": "update_version",
                })

        return resolutions

    async def build_dependency_graph(
        self,
        dependencies: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Build dependency graph.
        
        Args:
            dependencies: Package -> dependencies mapping
            
        Returns:
            Graph representation
        """
        graph = {
            "nodes": list(dependencies.keys()),
            "edges": [],
            "depth": {},
        }

        # Calculate depth
        def calculate_depth(package: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()

            if package in visited:
                return 0  # Circular dependency

            visited.add(package)

            deps = dependencies.get(package, [])
            if not deps:
                return 1

            return 1 + max(calculate_depth(d, visited.copy()) for d in deps)

        for package in dependencies:
            graph["depth"][package] = calculate_depth(package)
            for dep in dependencies[package]:
                graph["edges"].append((package, dep))

        return graph
