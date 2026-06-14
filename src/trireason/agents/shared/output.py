"""Shared output persistence utilities for all agents."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _get_output_dir() -> Path:
    """Get the base output directory for agent outputs."""
    base = Path(__file__).parent.parent.parent.parent / "output"
    base.mkdir(parents=True, exist_ok=True)
    return base


def save_agent_output(
    agent_name: str,
    data: dict[str, Any],
    iteration: int,
    output_dir: Path | None = None,
) -> Path:
    """Save agent output to a uniquely named JSON file.
    
    Args:
        agent_name: Name of the agent (e.g., 'generator', 'critic', 'refiner')
        data: Data to save (will be JSON-serialized)
        iteration: Iteration number (will be zero-padded to 3 digits)
        output_dir: Optional custom output directory
        
    Returns:
        Path to the saved file
    """
    if output_dir is None:
        output_dir = _get_output_dir() / agent_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    iteration_str = str(iteration).zfill(3)
    
    filename = f"{iteration_str}_{agent_name}_{timestamp}.json"
    filepath = output_dir / filename
    
    filepath.write_text(
        json.dumps(data, indent=2, default=str),
        encoding="utf-8",
    )
    
    return filepath
