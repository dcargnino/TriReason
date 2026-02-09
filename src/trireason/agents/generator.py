"""Generator agent – produces candidate prompts and simulated outputs."""

from __future__ import annotations

import json
import logging

from trireason.agents.llm import chat_json
from trireason.schemas.optimization import GeneratorOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the Generator agent in the TriReason prompt optimization system.

Your job:
1. Analyze the provided DATA and OBJECTIVE.
2. Design an effective AI prompt that will produce output fulfilling the objective.
3. The prompt you create should specify:
   - The AI role
   - Detailed task instructions
   - Constraints and guardrails
   - Expected output format
4. Simulate what a high-quality AI response to your prompt would look like, \
given the DATA.

Return a JSON object with exactly these keys:
{
  "candidate_prompt": "<the prompt you designed>",
  "candidate_output": "<simulated AI output for that prompt given the data>"
}
"""

SYSTEM_PROMPT_REFINE = """\
You are the Generator agent in the TriReason prompt optimization system.

You previously generated a prompt that was evaluated by the Critic agent. \
Based on the Critic's feedback and a refined prompt from the Refiner agent, \
generate an improved simulated output.

Your job:
1. Take the REFINED PROMPT and the original DATA.
2. Simulate a high-quality AI response that addresses all issues raised by the Critic.

Return a JSON object with exactly these keys:
{
  "candidate_prompt": "<the refined prompt, unchanged>",
  "candidate_output": "<improved simulated AI output>"
}
"""


async def generate_initial(data: str, objective: str, constraints: dict | None = None) -> GeneratorOutput:
    """Generate the first candidate prompt and simulated output."""
    user_msg_parts = [
        f"DATA:\n{data}",
        f"\nOBJECTIVE:\n{objective}",
    ]
    if constraints:
        user_msg_parts.append(f"\nCONSTRAINTS:\n{json.dumps(constraints, indent=2)}")

    raw = await chat_json(SYSTEM_PROMPT, "\n".join(user_msg_parts))
    parsed = json.loads(raw)
    return GeneratorOutput(**parsed)


async def generate_from_refinement(
    data: str,
    objective: str,
    refined_prompt: str,
    critic_issues: list[str],
    constraints: dict | None = None,
) -> GeneratorOutput:
    """Re-generate output using a refined prompt."""
    user_msg_parts = [
        f"DATA:\n{data}",
        f"\nOBJECTIVE:\n{objective}",
        f"\nREFINED PROMPT:\n{refined_prompt}",
        f"\nISSUES TO ADDRESS:\n" + "\n".join(f"- {i}" for i in critic_issues),
    ]
    if constraints:
        user_msg_parts.append(f"\nCONSTRAINTS:\n{json.dumps(constraints, indent=2)}")

    raw = await chat_json(SYSTEM_PROMPT_REFINE, "\n".join(user_msg_parts))
    parsed = json.loads(raw)
    return GeneratorOutput(**parsed)
