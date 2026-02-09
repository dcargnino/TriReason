"""Refiner agent – improves prompts based on Critic feedback."""

from __future__ import annotations

import json
import logging

from trireason.agents.llm import chat_json
from trireason.schemas.optimization import RefinerOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the Refiner agent in the TriReason prompt optimization system.

Given the current prompt, the Critic's evaluation, and the original objective, \
produce an improved version of the prompt.

Strategies to apply:
- Add missing constraints or instructions
- Remove ambiguity
- Enforce stricter output format
- Add guardrails against hallucination
- Improve determinism and reproducibility
- Address every issue the Critic raised
- Incorporate every recommendation

Do NOT change the fundamental intent of the prompt. Only improve quality.

Return a JSON object with exactly these keys:
{
  "refined_prompt": "<the improved prompt>",
  "changes_made": ["<change 1>", "<change 2>", ...]
}
"""


async def refine(
    current_prompt: str,
    objective: str,
    issues: list[str],
    recommendations: list[str],
    score_total: float,
) -> RefinerOutput:
    """Refine a prompt based on Critic feedback."""
    user_msg = (
        f"CURRENT PROMPT:\n{current_prompt}\n\n"
        f"OBJECTIVE:\n{objective}\n\n"
        f"CURRENT SCORE: {score_total}/100\n\n"
        f"ISSUES:\n" + "\n".join(f"- {i}" for i in issues) + "\n\n"
        f"RECOMMENDATIONS:\n" + "\n".join(f"- {r}" for r in recommendations)
    )
    raw = await chat_json(SYSTEM_PROMPT, user_msg)
    parsed = json.loads(raw)
    return RefinerOutput(**parsed)
