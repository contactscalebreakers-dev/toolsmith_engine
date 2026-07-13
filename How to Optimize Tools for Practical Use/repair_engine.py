"""
AI-Assisted Repair Engine for SB Toolsmith Pro

Uses LLM to generate intelligent repair suggestions.
"""

import logging
from typing import Optional, Dict, Any, List

from ..agents.repair_agent_enhanced import RecoveryStrategy

logger = logging.getLogger(__name__)


class AIRepairEngine:
    """AI-powered repair suggestion engine."""

    def __init__(self, provider: Any):
        """
        Initialize repair engine.
        
        Args:
            provider: LLM provider
        """
        self.provider = provider

    async def suggest_repairs(
        self,
        error_message: str,
        tool_name: str,
        diagnostics: Dict[str, Any],
        max_suggestions: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate repair suggestions using LLM.
        
        Args:
            error_message: Error message
            tool_name: Tool that failed
            diagnostics: Diagnostic information
            max_suggestions: Maximum suggestions to generate
            
        Returns:
            List of repair suggestions
        """
        # Build diagnostic summary
        diagnostic_summary = self._format_diagnostics(diagnostics)

        # Build prompt
        prompt = f"""You are an expert Python developer and debugging specialist.

Tool: {tool_name}
Error: {error_message}

Diagnostic Information:
{diagnostic_summary}

Generate up to {max_suggestions} specific, actionable repair suggestions.

For each suggestion, provide:
1. Title (short description)
2. Description (detailed explanation)
3. Steps (numbered list of steps to implement)
4. Risk Level (low/medium/high)
5. Estimated Time (minutes)
6. Success Probability (0-100%)

Format each suggestion clearly."""

        response = await self.provider.generate(
            prompt,
            system="You are a Python debugging expert. Provide practical, actionable repair suggestions.",
            temperature=0.5,
        )

        # Parse suggestions
        suggestions = self._parse_suggestions(response)
        return suggestions[:max_suggestions]

    async def analyze_failure_pattern(
        self,
        error_message: str,
        stderr: str,
        stdout: str,
        source_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze failure pattern using LLM.
        
        Args:
            error_message: Error message
            stderr: Standard error output
            stdout: Standard output
            source_code: Optional source code
            
        Returns:
            Analysis results
        """
        prompt = f"""Analyze this Python execution failure and provide insights.

Error: {error_message}

Stderr:
{stderr[:500]}

Stdout:
{stdout[:500]}

{f"Source Code Snippet:{chr(10)}{source_code[:500]}" if source_code else ""}

Provide:
1. Root Cause Analysis (1-2 sentences)
2. Error Category (import, syntax, runtime, etc.)
3. Severity Level (critical/high/medium/low)
4. Affected Components (list)
5. Preventive Measures (list)"""

        response = await self.provider.generate(
            prompt,
            system="You are a Python debugging expert. Analyze failures and provide insights.",
            temperature=0.3,
        )

        return {
            "analysis": response,
            "timestamp": self._get_timestamp(),
        }

    async def generate_recovery_plan(
        self,
        tool_name: str,
        error_type: str,
        available_strategies: List[RecoveryStrategy],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recovery plan.
        
        Args:
            tool_name: Tool name
            error_type: Type of error
            available_strategies: Available recovery strategies
            
        Returns:
            Recovery plan
        """
        # Format strategies
        strategies_text = "\n".join([
            f"- {s.strategy_type}: {s.description} (Success: {s.success_probability:.0%}, Risk: {s.risk_level})"
            for s in available_strategies
        ])

        prompt = f"""Create a comprehensive recovery plan for the following failure.

Tool: {tool_name}
Error Type: {error_type}

Available Recovery Strategies:
{strategies_text}

Provide:
1. Recommended Strategy (with justification)
2. Step-by-Step Recovery Plan
3. Success Indicators (how to verify recovery)
4. Rollback Plan (if needed)
5. Prevention Measures (for future)"""

        response = await self.provider.generate(
            prompt,
            system="You are a system recovery specialist. Create detailed, practical recovery plans.",
            temperature=0.4,
        )

        return {
            "plan": response,
            "tool": tool_name,
            "error_type": error_type,
            "timestamp": self._get_timestamp(),
        }

    async def explain_error(self, error_message: str) -> str:
        """
        Explain an error in simple terms.
        
        Args:
            error_message: Error message
            
        Returns:
            Explanation
        """
        prompt = f"""Explain this Python error in simple, non-technical terms that a beginner can understand.

Error: {error_message}

Provide:
1. What happened (simple explanation)
2. Why it happened (common causes)
3. How to fix it (simple steps)"""

        explanation = await self.provider.generate(
            prompt,
            system="You are a helpful Python tutor. Explain errors clearly and simply.",
            temperature=0.5,
        )

        return explanation

    def _format_diagnostics(self, diagnostics: Dict[str, Any]) -> str:
        """Format diagnostics for prompt."""
        lines = []

        error_analysis = diagnostics.get("error_analysis", {})
        lines.append(f"Error Type: {error_analysis.get('error_type', 'unknown')}")
        lines.append(f"Categories: {', '.join(error_analysis.get('error_categories', []))}")

        code_analysis = diagnostics.get("code_analysis", {})
        if code_analysis.get("has_syntax_errors"):
            lines.append("Has Syntax Errors: Yes")
        if code_analysis.get("imports"):
            lines.append(f"Imports: {', '.join(code_analysis['imports'][:5])}")

        env_analysis = diagnostics.get("environment_analysis", {})
        if env_analysis.get("python_version"):
            lines.append(f"Python Version: {env_analysis['python_version']}")

        return "\n".join(lines)

    def _parse_suggestions(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM suggestions."""
        # Simple parsing - in production, use structured output
        suggestions = []

        # Split by numbered suggestions
        parts = response.split("\n\n")

        for part in parts:
            if not part.strip():
                continue

            suggestion = {
                "title": "Repair Suggestion",
                "description": part[:200],
                "steps": [part],
                "risk_level": "medium",
                "estimated_time": 30,
                "success_probability": 0.7,
            }
            suggestions.append(suggestion)

        return suggestions

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
