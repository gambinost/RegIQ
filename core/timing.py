"""Agent timing tracking utilities for the RegIQ cascade pipeline."""

from __future__ import annotations

import json
import re
import time
from typing import Any

TIMING_PATTERN = re.compile(r"<!--\s*REGIQ_TIMING:\s*(.*?)-->", re.DOTALL)


def extract_timing_blocks(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Remove timing HTML comments from message text and return the data."""
    blocks: list[dict[str, Any]] = []

    def _extract(match: re.Match) -> str:
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, dict) and "agent" in data:
                blocks.append(data)
        except json.JSONDecodeError:
            pass
        return ""

    cleaned = TIMING_PATTERN.sub(_extract, text).strip()
    return cleaned, blocks


def append_timing_block(text: str, agent_name: str, duration: float) -> str:
    """Append a timing block to the message text."""
    timing_data = {"agent": agent_name, "duration": round(duration, 2)}
    return f"{text}\n\n<!-- REGIQ_TIMING: {json.dumps(timing_data)} -->"


def build_timing_dict(blocks: list[dict[str, Any]]) -> dict[str, float]:
    """Build the timing dict from collected blocks."""
    timing: dict[str, float] = {}
    total = 0.0
    for block in blocks:
        agent = block.get("agent", "unknown")
        duration = block.get("duration", 0.0)
        timing[agent] = duration
        total += duration
    if timing:
        timing["total"] = round(total, 2)
    return timing


def format_timing_for_display(timing: dict[str, float]) -> str:
    """Format timing data for console logs."""
    lines = ["[TIMING] Pipeline timing:"]
    for agent, duration in timing.items():
        if agent == "total":
            lines.append(f"  Total: {duration}s")
        else:
            lines.append(f"  {agent}: {duration}s")
    return "\n".join(lines)


class AgentTimer:
    """Context manager for timing an agent's execution."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time: float | None = None
        self.duration: float = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.duration = round(time.time() - self.start_time, 2)
        return False

    def elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        return round(time.time() - self.start_time, 2)


try:
    import httpx
except ImportError:
    httpx = None


async def post_heartbeat(agent_name: str, status: str, duration: float | None = None) -> None:
    """Post an agent status update to the FastAPI pipeline status endpoint."""
    if httpx is None:
        return
    try:
        from core.settings import get_settings

        settings = get_settings()
        url = f"{settings.REGIQ_API_BASE_URL}/api/v1/hitl/pipeline/status/default"
        payload = {"agent": agent_name, "status": status}
        if duration is not None:
            payload["duration"] = duration
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=5.0)
    except Exception:
        pass
