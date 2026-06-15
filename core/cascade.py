from band.runtime.tools import AgentToolsProtocol

from utils.loggers import log_success, log_warning

CASCADE_SLUGS = {
    "monitor": "legal-parser",
    "legal_parser": "impact-mapper",
    "impact_mapper": "gap-analyst",
    "gap_analyst": "planner",
    "remediation_planner": None,
}


async def resolve_cascade_target(
    tools: AgentToolsProtocol,
    source_agent: str,
    cached_handle: str | None = None,
) -> tuple[str, str | None]:
    if cached_handle is not None:
        return cached_handle, cached_handle

    target_slug = CASCADE_SLUGS.get(source_agent)
    if target_slug is None:
        log_warning(f"No cascade target defined for agent '{source_agent}'")
        return "", None

    try:
        participants = await tools.get_participants()
        for p in participants:
            handle = getattr(p, "handle", None) or (
                p.get("handle", "") if isinstance(p, dict) else ""
            )
            if target_slug in handle:
                log_success(f"Resolved cascade target: {handle}")
                return target_slug, handle
    except Exception as e:
        log_warning(f"Could not resolve cascade target from participants: {e}")

    log_warning(f"Could not find '{target_slug}' in participants, using fallback")
    return target_slug, target_slug


def get_cascade_slug(agent_name: str) -> str | None:
    return CASCADE_SLUGS.get(agent_name)
