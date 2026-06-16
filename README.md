# RegIQ — Regulatory Change Intelligence System

> **Band of Agents Hackathon** — June 12-19, 2026

RegIQ is a 5-agent cascade pipeline that ingests new regulations, parses legal requirements, maps them to company processes, identifies compliance gaps, and generates prioritized remediation tickets with human-in-the-loop approval.

```
Monitor → Legal Parser → Impact Mapper → Gap Analyst → Remediation Planner
```

---

## Architecture

### Agent Pipeline

| # | Agent | Model | Role | Cascade Target |
|---|-------|-------|------|----------------|
| 1 | **Monitor** | Gemini-2.5-Flash | Assess regulation urgency | `@regiq-legal-parser` |
| 2 | **Legal Parser** | Claude Sonnet | Extract requirements | `@regiq-impact-mapper` |
| 3 | **Impact Mapper** | Claude Sonnet | Map to company processes (RAG) | `@regiq-gap-analyst` |
| 4 | **Gap Analyst** | Claude Sonnet | Identify compliance gaps | `@regiq-planner` |
| 5 | **Remediation Planner** | Claude Sonnet | Generate remediation tickets | **TERMINAL** (no cascade) |

### Communication Protocol

All agents communicate via the Band SDK (`thenvoi`). Each agent receives a JSON payload from the previous agent, processes it with an LLM, and forwards results by @mentioning the next agent in the cascade.

The Remediation Planner is the **terminal agent**. Instead of forwarding, it:
1. Generates the final `ComplianceReport` with sequenced `RemediationTicket` objects
2. **POSTs the report via webhook to FastAPI** (`POST /api/v1/hitl/report/{regulation_id}`)
3. Posts a human-readable summary to the Band chat room

### Webhook Integration (Critical)

The Remediation Planner agent does not rely on mock data. When it finishes generating tickets, it makes an HTTP POST to the FastAPI backend:

```python
# In agents/remediation_planner/agent.py
import httpx

async def _submit_report_to_api(report: ComplianceReport):
    await httpx.post(
        f"{API_BASE_URL}/api/v1/hitl/report/{report.regulation_id}",
        json=report.model_dump(),
        timeout=30.0,
    )
```

FastAPI stores this in an in-memory cache (sufficient for demo). The frontend HITL review page fetches the **real generated report** from this endpoint.

**Mock data** in `api/routes/hitl.py` exists **only as a fallback** for frontend development and UI testing. In production/demo mode, the mock is bypassed when a real report exists.

---

## Judge Demo Flow

### Step 1: Trigger Page (`/`)

Judges land on a trigger page with two options:

**Option A — Select Pre-loaded Regulation**
- Dropdown with 3 regulations:
  - `GDPR-2026-003` — EU Enhanced Right to Erasure (30-day mandate)
  - `SEC-2026-001` — US SEC Cybersecurity Risk Management
  - `APAC-2026-002` — APAC Data Localization Requirements
- Click **"Run Compliance Analysis"**

**Option B — Draft Custom Regulation**
- Textarea for free-form regulation text
- Optional fields: jurisdiction, effective date, penalty amount
- Click **"Run Compliance Analysis"**

### Step 2: Pipeline Visualization (`/pipeline`)

After triggering, judges see a real-time pipeline visualization:

```
[Monitor] → [Legal Parser] → [Impact Mapper] → [Gap Analyst] → [Remediation Planner]
   🟢         ⚪              ⚪                ⚪              ⚪
```

- Nodes pulse/animate when that agent is processing
- Status indicators: ⚪ idle / 🟡 processing / 🟢 complete / 🔴 error
- Connecting lines animate with a traveling dot when messages flow between agents
- Each node shows: agent name, model used, last message timestamp
- A log panel below shows the actual message content flowing through the pipeline

This visualization **polls the Band room** (or uses Server-Sent Events from FastAPI) to reflect real agent activity.

### Step 3: HITL Review (`/review/{regulation_id}`)

When the Remediation Planner completes:
- Auto-redirect from pipeline page to HITL review
- Shows the **real generated report** with:
  - Regulation header + status badge
  - Summary bar: total gaps, critical gaps, weeks to deadline, critical path weeks
  - Executive summary
  - Sequencing note
  - Ticket cards with: priority (Critical/High/Medium), gap_ref tag, dependency pills, numbered action list, done criteria
- Sticky action bar: **Approve** or **Reject** with reason
- Confirm modal with focus trap and escape key handling

### Step 4: Decision Confirmation

After approving/rejecting:
- Status banner shows result
- Option to "Run Another Regulation" returns to trigger page
- Decision is stored in FastAPI and visible in the Band chat room

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | Band SDK (`thenvoi`) + LangGraph adapters |
| LLM Routing | AI/ML API (OpenAI-compatible) |
| Models | Gemini-2.5-Flash (fast), Claude Sonnet (reasoning) |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | Qdrant Cloud |
| Backend | FastAPI + Python 3.11 |
| Frontend | Vite + React 19 + TypeScript + Tailwind CSS v4 |
| Observability | LangSmith (LLM tracing) |
| Deployment | Uvicorn (backend), Vite dev server (frontend) |

---

## LangSmith Setup

LangSmith traces are **essential for the demo**. They prove to judges that agents are actually calling LLMs with real prompts.

### Setup

1. Get API key: https://smith.langchain.com
2. Add to `.env`:
   ```
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=ls-...
   LANGSMITH_PROJECT=RegIQ-Hackathon
   ```
3. Traces are automatic — every `ChatOpenAI` call in `core/llm.py` is instrumented

### What to Show Judges

- Open https://smith.langchain.com
- Filter project "RegIQ-Hackathon"
- Show the cascade trace tree:
  ```
  Run: Monitor-GDPR-2026-003
  ├── Monitor Agent
  │   ├── Prompt: MONITOR_SYSTEM_PROMPT + regulation_text
  │   └── Output: RegulationAssessment JSON
  ├── Legal Parser Agent
  │   ├── Prompt: LEGAL_PARSER_SYSTEM_PROMPT + assessment
  │   └── Output: ParsedRequirements JSON
  ...etc
  ```
- Click any trace to show exact prompt tokens, latency, model name
- This demonstrates transparency and debuggability

---

## Implementation Checklist

### Critical Path (Do First)

- [ ] **Webhook from Planner to FastAPI**
  - Add `httpx` POST in `agents/remediation_planner/agent.py`
  - Add `POST /api/v1/hitl/report/{regulation_id}` endpoint in `api/routes/hitl.py`
  - In-memory store for generated reports
  - Frontend fetches real report, falls back to mock only if none exists

- [ ] **Frontend Trigger Page**
  - `frontend/src/pages/TriggerPage.tsx`
  - Dropdown with 3 regulations (reads from `data/mock_regulations/*.json`)
  - Custom regulation textarea
  - "Run Analysis" button with loading state
  - POST to `/api/v1/trigger` (or directly calls Band SDK if trigger endpoint not ready)

- [ ] **Pipeline Visualization Page**
  - `frontend/src/pages/PipelineViz.tsx`
  - 5 nodes in horizontal flow
  - Animated status indicators
  - Poll Band room or FastAPI status endpoint for real-time updates
  - Log panel showing message previews

### High Priority

- [ ] **Trigger Endpoint in FastAPI**
  - `api/routes/trigger.py`
  - `POST /api/v1/trigger`
  - Accepts `regulation_id` or full regulation payload
  - Creates Band room, adds Monitor agent, sends regulation with @mention
  - Returns `{room_id, status: "cascade_started"}`

- [ ] **Real-time Status Polling**
  - `GET /api/v1/pipeline/status/{room_id}`
  - Returns which agents have completed
  - Frontend uses this to animate the pipeline viz

### Medium Priority

- [ ] **Additional Test Regulations**
  - `data/mock_regulations/sec_cybersecurity_2026.json`
  - `data/mock_regulations/apac_localization_2026.json`

- [ ] **Polish**
  - Mobile responsiveness for pipeline viz
  - Dark mode consistency across all pages
  - Loading skeletons for trigger → pipeline → review transitions

---

## File Structure

```
RegIQ/
├── agents/
│   ├── monitor/               # Agent 1 — urgency assessment
│   ├── legal_parser/          # Agent 2 — requirement extraction
│   ├── impact_mapper/         # Agent 3 — process mapping (RAG)
│   ├── gap_analyst/           # Agent 4 — gap identification
│   └── remediation_planner/   # Agent 5 — ticket generation (TERMINAL)
├── api/
│   └── routes/
│       ├── hitl.py            # HITL endpoints + mock fallback
│       ├── trigger.py         # Pipeline trigger endpoint
│       └── health.py          # Health checks
├── core/
│   ├── settings.py            # Env/config
│   ├── llm.py                 # LLM factory
│   ├── cascade.py             # Agent routing
│   └── band_client.py         # Band room helpers
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── TriggerPage.tsx      # Regulation selection + custom draft
│   │   │   ├── PipelineViz.tsx      # Real-time agent flow visualization
│   │   │   └── ReviewPage.tsx       # HITL approval interface
│   │   ├── components/
│   │   │   ├── HITLReview.tsx       # Main review layout
│   │   │   ├── TicketCard.tsx       # Individual ticket display
│   │   │   ├── SummaryBar.tsx       # Gap metrics
│   │   │   ├── PipelineNode.tsx     # Single agent node for viz
│   │   │   └── ConnectionLine.tsx   # Animated connector
│   │   ├── api.ts             # API client
│   │   └── types.ts           # TypeScript interfaces
│   └── vite.config.ts         # Vite + Tailwind + proxy
├── models/
│   ├── regulation.py          # RegulationAssessment
│   ├── requirement.py         # ParsedRequirements
│   ├── impact.py              # ImpactAssessment
│   ├── gap.py                 # GapAnalysis
│   └── report.py              # ComplianceReport + RemediationTicket
├── data/
│   └── mock_regulations/      # Test regulation JSONs
├── main.py                    # FastAPI entry point
└── README.md                  # This file
```

---

## Quick Start (for Development)

```bash
# 1. Backend
python main.py                    # Starts FastAPI on :8000

# 2. Frontend (new terminal)
cd frontend && npm run dev        # Starts Vite on :5173

# 3. Agents (5 terminals)
python agents/monitor/agent.py
python agents/legal_parser/agent.py
python agents/impact_mapper/agent.py
python agents/gap_analyst/agent.py
python agents/remediation_planner/agent.py

# 4. Open frontend
open http://localhost:5173
```

---

## Key Design Decisions

### Why SimpleAdapter, not LangGraphAdapter with interrupt()?

All 5 agents use `SimpleAdapter` for consistency. The HITL gate is handled by the FastAPI backend + frontend, not by LangGraph's `interrupt()`. This decouples agent execution from human approval and allows the frontend to be the single source of truth for HITL state.

### Why Webhook from Terminal Agent?

Band is a message bus, not a database. Chat messages are ephemeral and unstructured. The Remediation Planner POSTs structured JSON to FastAPI so the frontend can fetch a validated `ComplianceReport` object. Without this, the frontend would need to parse chat messages — fragile and error-prone.

### Why Mock Data Exists

The mock report in `api/routes/hitl.py` serves two purposes:
1. **Frontend development** — UI can be built and styled before the agent is ready
2. **Demo fallback** — If the agent fails or LLM API is down, the HITL page still renders

In production/demo mode, the mock is **only used when no real report has been generated**.

---

## Contact

Built for the **Band of Agents Hackathon** (lablab.ai, June 2026).
