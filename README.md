# RegIQ — Regulatory Change Intelligence System

> **Band of Agents Hackathon** — June 12-19, 2026

RegIQ is a 5-agent cascade pipeline that ingests new regulations, parses legal requirements, maps them to company processes, identifies compliance gaps, and generates prioritized remediation tickets with human-in-the-loop approval.

```
Monitor → Legal Parser → Impact Mapper → Gap Analyst → Remediation Planner
```

## How It Works

1. **Trigger** — Select a regulation or draft your own
2. **Pipeline** — Watch 5 AI agents analyze it in real-time
3. **Review** — Inspect prioritized remediation tickets with dependency chains
4. **Decide** — Approve or reject the plan with one click

## Quick Start

```bash
# Backend
python main.py                    # FastAPI on http://localhost:8000

# Frontend
cd frontend && npm run dev        # Vite on http://localhost:5173

# Agents (5 terminals)
python agents/monitor/agent.py
python agents/legal_parser/agent.py
python agents/impact_mapper/agent.py
python agents/gap_analyst/agent.py
python agents/remediation_planner/agent.py
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agents | Band SDK + LangGraph + LangChain |
| LLMs | Gemini-2.5-Flash, Claude Sonnet (via AI/ML API) |
| Backend | FastAPI + Python 3.11 |
| Frontend | Vite + React 19 + TypeScript + Tailwind CSS v4 |
| Vector DB | Qdrant Cloud |
| Observability | LangSmith |

## License

MIT
