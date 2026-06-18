"""RegIQ Trigger API — start the cascade pipeline and list test regulations.

Endpoints:
    POST /api/v1/trigger              — Create a Band room, add Monitor, send regulation
    GET  /api/v1/trigger/regulations  — List available test regulations from data/mock_regulations/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.band_client import trigger_pipeline
from utils.loggers import log_info, log_error

router = APIRouter(prefix="/api/v1", tags=["trigger"])

_MOCK_REGULATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "mock_regulations"


class TriggerRequest(BaseModel):
    regulation_id: str | None = None
    regulation_text: str | None = None
    regulation_title: str | None = None
    target_handle: str | None = None


class TriggerResponse(BaseModel):
    status: str = "triggered"
    room_id: str
    regulation_title: str | None = None


class RegulationOption(BaseModel):
    regulation_id: str
    title: str
    jurisdiction: str
    summary: str
    industry_tags: list[str]


@router.post("/trigger", response_model=TriggerResponse)
async def trigger_cascade(request: TriggerRequest):
    """Trigger the RegIQ cascade pipeline by sending a regulation to the Monitor agent.

    Creates a Band chat room, adds the Monitor agent as a participant,
    and sends the regulation text mentioning the Monitor. The Monitor
    will process the regulation and cascade through the pipeline.
    """
    if request.regulation_id:
        json_file = _MOCK_REGULATIONS_DIR / f"{request.regulation_id}.json"
        if not json_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Regulation file not found: {request.regulation_id}",
            )
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            regulation_text = data.get("full_text", "")
            if not regulation_text:
                raise HTTPException(
                    status_code=422,
                    detail=f"Regulation {request.regulation_id} has no full_text field",
                )
        except (json.JSONDecodeError, KeyError) as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse regulation file {request.regulation_id}: {e}",
            )
    elif request.regulation_text:
        regulation_text = request.regulation_text
    else:
        raise HTTPException(
            status_code=400,
            detail="Either regulation_id or regulation_text is required",
        )

    log_info(
        f"Trigger request received: "
        f"{request.regulation_title or request.regulation_id or 'custom text'}"
    )

    try:
        room_id = await trigger_pipeline(
            regulation_text=regulation_text,
            target_handle=request.target_handle,
        )
        log_info(f"Cascade triggered in room {room_id}")
        return TriggerResponse(
            room_id=room_id,
            regulation_title=request.regulation_title,
        )
    except ValueError as e:
        log_error(f"Trigger failed (peer not found): {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        log_error(f"Trigger failed (unexpected): {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger cascade: {e}")


@router.get("/trigger/regulations", response_model=list[RegulationOption])
async def list_test_regulations():
    """List available test regulations from data/mock_regulations/.

    Returns metadata for each JSON file so the frontend can populate
    a regulation picker dropdown.
    """
    options: list[RegulationOption] = []

    if not _MOCK_REGULATIONS_DIR.exists():
        return options

    for json_file in sorted(_MOCK_REGULATIONS_DIR.glob("*.json")):
        try:
            data: dict[str, Any] = json.loads(json_file.read_text(encoding="utf-8"))
            options.append(
                RegulationOption(
                    regulation_id=data.get("regulation_id", json_file.stem),
                    title=data.get("title", json_file.stem),
                    jurisdiction=data.get("jurisdiction", "Unknown"),
                    summary=data.get("summary", ""),
                    industry_tags=data.get("industry_tags", []),
                )
            )
        except (json.JSONDecodeError, KeyError) as e:
            log_error(f"Skipping malformed regulation file {json_file.name}: {e}")

    return options
