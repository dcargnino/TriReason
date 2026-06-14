"""Refiner agent – improves prompts based on Critic feedback."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from trireason.agents.shared.llm import chat_json
from trireason.agents.shared.output import save_agent_output
from trireason.schemas.optimization import RefinerOutput

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


async def refine(
    current_system_message: str,
    objective: str,
    data: str,
    critic_feedback: dict,
    quality_threshold: int = 100,
    iteration: int = 1,
) -> RefinerOutput:
    """Refine the Generator's system message based on Critic feedback."""
    user_msg = _render_template(
        USER_TEMPLATE,
        objective=objective,
        data=data,
        iteration=iteration,
        current_system_message=current_system_message,
        critic_feedback=critic_feedback,
        quality_threshold=quality_threshold,
    )
    raw = await chat_json(SYSTEM_PROMPT, user_msg)
    parsed = json.loads(raw)
    result = RefinerOutput(**parsed)
    
    save_agent_output(
        "refiner",
        {
            "iteration": iteration,
            "input": {
                "current_system_message": current_system_message,
                "objective": objective,
                "data": data,
                "critic_feedback": critic_feedback,
                "quality_threshold": quality_threshold,
            },
            "output": result.model_dump(),
        },
        iteration=iteration,
    )
    
    return result
