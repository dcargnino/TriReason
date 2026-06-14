"""Critic agent – evaluates the quality of generated output against the objective."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from trireason.agents.shared.llm import chat_json
from trireason.agents.shared.output import save_agent_output
from trireason.schemas.optimization import CriticOutput

logger = logging.getLogger(__name__)

_AGENT_DIR = Path(__file__).parent

def _load_text(path: Path) -> str:
    """Load text content from a file."""
    return path.read_text(encoding="utf-8")

SYSTEM_PROMPT = _load_text(_AGENT_DIR / "system_prompt.md")
USER_TEMPLATE = _load_text(_AGENT_DIR / "user_prompt.md")


def _render_template(template: str, **kwargs) -> str:
    """Render a template by replacing {{placeholder}} with values."""
    result = template
    for key, value in kwargs.items():
        placeholder = f"{{{{{key}}}}}"
        if value is None:
            value = ""
        elif isinstance(value, dict):
            value = json.dumps(value, indent=2)
        elif isinstance(value, list):
            value = "\n".join(f"- {item}" for item in value)
        result = result.replace(placeholder, str(value))
    return result


async def critique(
    data: str,
    objective: str,
    candidate_output: str,
    iteration: int = 1,
) -> CriticOutput:
    """Evaluate a candidate output and return structured scores."""
    user_msg = _render_template(USER_TEMPLATE, data=data, objective=objective, iteration=iteration, output=candidate_output)
    raw = await chat_json(SYSTEM_PROMPT, user_msg)
    parsed = json.loads(raw)
    result = CriticOutput(**parsed)
    
    save_agent_output(
        "critic",
        {
            "iteration": iteration,
            "input": {"data": data, "objective": objective, "candidate_output": candidate_output},
            "output": result.model_dump(),
        },
        iteration=iteration,
    )
    
    return result
