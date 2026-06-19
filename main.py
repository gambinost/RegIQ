import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes.health import base_router as health_router
from api.routes.hitl import router as hitl_router
from api.routes.regulations import router as regulations_router
from core.settings import get_settings
from rich.console import Console

console = Console()
settings = get_settings()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.include_router(health_router)
app.include_router(hitl_router)
app.include_router(regulations_router)

# CORS — allow all origins for hackathon demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React frontend (must be after API routes)
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")


# ── Agent subprocess management ──────────────────────────────────────────────
agent_processes: list[subprocess.Popen] = []


@app.on_event("startup")
async def start_agents():
    """Start all 5 cascade agents as background processes."""
    global agent_processes

    agents = [
        "agents.monitor.agent",
        "agents.legal_parser.agent",
        "agents.impact_mapper.agent",
        "agents.gap_analyst.agent",
        "agents.remediation_planner.agent",
    ]

    for agent_module in agents:
        console.print(f"[bold cyan]Starting agent:[/bold cyan] {agent_module}")
        p = subprocess.Popen(
            [sys.executable, "-m", agent_module],
            cwd=str(Path(__file__).parent),
        )
        agent_processes.append(p)

    console.print(f"[bold green]✓ All {len(agent_processes)} agents started[/bold green]")


@app.on_event("shutdown")
async def stop_agents():
    """Terminate all agent processes on shutdown."""
    for p in agent_processes:
        if p.poll() is None:  # still running
            p.terminate()
    console.print("[bold yellow]All agents stopped[/bold yellow]")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_RELOAD
    )
