"""Generator agent – produces candidate prompts and simulated outputs."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from trireason.agents.shared.llm import chat_json
from trireason.agents.shared.output import save_agent_output
from trireason.schemas.optimization import GeneratorOutput

logger = logging.getLogger(__name__)

_AGENT_DIR = Path(__file__).parent

def _load_text(path: Path) -> str:
    """Load text content from a file."""
    return path.read_text(encoding="utf-8")

SYSTEM_PROMPT = _load_text(_AGENT_DIR / "system_prompt.md")
USER_TEMPLATE = _load_text(_AGENT_DIR / "user_prompt.md")
USER_TEMPLATE_REFINE = _load_text(_AGENT_DIR / "user_prompt_refine.md")


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


async def generate_initial(data: str, objective: str, constraints: dict | None = None, iteration: int = 1) -> GeneratorOutput:
    """Generate the first candidate prompt and simulated output."""
    user_msg = _render_template(USER_TEMPLATE, data=data, objective=objective, iteration=iteration, constraints=constraints)
    raw = await chat_json(SYSTEM_PROMPT, user_msg)
    parsed = json.loads(raw)
    result = GeneratorOutput(**parsed)
    
    save_agent_output(
        "generator",
        {
            "type": "initial",
            "iteration": iteration,
            "input": {"data": data, "objective": objective, "constraints": constraints},
            "output": result.model_dump(),
        },
        iteration=iteration,
    )
    
    return result


async def generate_from_refinement(
    data: str,
    objective: str,
    refined_prompt: str,
    critic_issues: list[str],
    constraints: dict | None = None,
    iteration: int = 1,
) -> GeneratorOutput:
    """Re-generate output using a refined prompt."""
    user_msg = _render_template(
        USER_TEMPLATE_REFINE,
        data=data,
        objective=objective,
        iteration=iteration,
        refined_prompt=refined_prompt,
        critic_issues=critic_issues,
        constraints=constraints,
    )
    raw = await chat_json(SYSTEM_PROMPT, user_msg)
    parsed = json.loads(raw)
    result = GeneratorOutput(**parsed)
    
    save_agent_output(
        "generator",
        {
            "type": "refined",
            "iteration": iteration,
            "input": {
                "data": data,
                "objective": objective,
                "refined_prompt": refined_prompt,
                "critic_issues": critic_issues,
                "constraints": constraints,
            },
            "output": result.model_dump(),
        },
        iteration=iteration,
    )
    
    return result
