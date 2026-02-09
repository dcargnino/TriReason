"""Critic agent – evaluates the quality of generated output against the objective."""

from __future__ import annotations

import json
import logging

from trireason.agents.llm import chat_json
from trireason.schemas.optimization import CriticOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the Critic agent in the TriReason prompt optimization system.

You evaluate the OUTPUT (not the prompt) against the stated OBJECTIVE and DATA.

Score the output on these weighted categories (each 0-100):

| Category                  | Weight |
|---------------------------|--------|
| Objective fulfillment     | 40%    |
| Correctness & faithfulness| 25%    |
| Completeness              | 15%    |
| Format compliance         | 10%    |
| Clarity & usability       | 10%    |

Compute the total weighted score (0-100).

Return a JSON object with exactly these keys:
{
  "score_total": <weighted total 0-100>,
  "score_breakdown": {
    "objective_fulfillment": <0-100>,
    "correctness_faithfulness": <0-100>,
    "completeness": <0-100>,
    "format_compliance": <0-100>,
    "clarity_usability": <0-100>
  },
  "passed": <true if score_total >= THRESHOLD, else false>,
  "issues": ["<issue 1>", "<issue 2>", ...],
  "recommendations": ["<actionable improvement 1>", ...]
}

Be rigorous. Identify concrete, fixable issues. Recommendations should be \
specific enough for the Refiner agent to act on.
"""


async def critique(
    data: str,
    objective: str,
    candidate_prompt: str,
    candidate_output: str,
    threshold: int = 85,
) -> CriticOutput:
    """Evaluate a candidate output and return structured scores."""
    user_msg = (
        f"DATA:\n{data}\n\n"
        f"OBJECTIVE:\n{objective}\n\n"
        f"PROMPT USED:\n{candidate_prompt}\n\n"
        f"OUTPUT TO EVALUATE:\n{candidate_output}\n\n"
        f"PASS THRESHOLD: {threshold}"
    )
    raw = await chat_json(SYSTEM_PROMPT, user_msg)
    parsed = json.loads(raw)
    return CriticOutput(**parsed)
