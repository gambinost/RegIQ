"""Band REST API client for triggering the RegIQ cascade pipeline.

Wraps the thenvoi_rest AsyncRestClient to:
1. Resolve the sender agent's own identity via GET /agent/me
2. Find the other 4 cascade agents via GET /agent/peers
3. Create a Band chat room
4. Add ALL 5 cascade agents as participants
5. Send a regulation message mentioning only the Monitor (the cascade
   entry point)

Uses the Band REST API's canonical identity endpoint (agent_api_identity.
get_agent_me) to discover the sender's own handle — the same pattern the
SDK uses internally in platform_runtime.py. No peer-search glue for the
sender; it cannot appear in its own peer list.
"""

from __future__ import annotations

import logging

from thenvoi_rest import (
    AsyncRestClient,
    ChatMessageRequest,
    ChatMessageRequestMentionsItem,
    ChatRoomRequest,
    ParticipantRequest,
)
from thenvoi_rest.core.request_options import RequestOptions

from core.band_config import get_agent_credentials, get_band_rest_url
from utils.loggers import log_info, log_success, log_error, log_warning

logger = logging.getLogger(__name__)

DEFAULT_REQUEST_OPTIONS: RequestOptions = {"max_retries": 3}

# The agent whose API key authenticates the REST calls. This agent becomes
# the room creator / message sender. Using the Planner (terminal agent) so
# the Monitor — the cascade entry point — is a separate participant and
# its on_message fires when @mentioned.
SENDER_AGENT_NAME = "remediation_planner"

# All 5 cascade agents in order. Each entry is (role, handle_fragment).
# The handle fragment is matched case-insensitively as a substring of the
# peer's handle. All 5 MUST be added as participants before the cascade
# starts, because core/cascade.py resolves the next agent by calling
# get_participants() and searching for the target slug in handles.
CASCADE_AGENTS: list[tuple[str, str]] = [
    ("monitor", "regiq-monitor"),
    ("legal_parser", "regiq-legal-parser"),
    ("impact_mapper", "regiq-impact-mapper"),
    ("gap_analyst", "regiq-gap-analyst"),
    ("remediation_planner", "regiq-planner"),
]

# The Monitor is the cascade entry point — only it is @mentioned in the
# initial regulation message. Subsequent agents are @mentioned by the
# upstream agent's on_message via core/cascade.py.
ENTRY_AGENT_ROLE = "monitor"

# The role of the sender agent (resolved via get_agent_me, not peer search).
SENDER_ROLE = "remediation_planner"


async def _get_self_identity(client: AsyncRestClient) -> dict[str, str]:
    """Fetch the authenticated agent's own identity via GET /agent/me.

    This is the canonical way to discover the sender's own id and handle.
    An agent cannot appear in its own peer list, so peer search would
    never find it — get_agent_me is the correct API.
    """
    response = await client.agent_api_identity.get_agent_me(
        request_options=DEFAULT_REQUEST_OPTIONS,
    )
    agent = response.data
    return {
        "id": agent.id,
        "name": agent.name,
        "handle": agent.handle,
    }


async def _find_cascade_peers(
    client: AsyncRestClient,
    exclude_handle: str | None = None,
) -> dict[str, dict[str, str]]:
    """Fetch agent peers and match them to cascade roles by handle fragment.

    Args:
        client: The authenticated AsyncRestClient.
        exclude_handle: If provided, skip peers whose handle matches this
            (the sender — already resolved via get_agent_me).

    Returns a dict mapping role -> {"id", "name", "handle"} for each found
    agent. The sender role is NOT included here; it's added separately
    from get_agent_me. Agents not found are omitted.
    """
    found: dict[str, dict[str, str]] = {}
    # Only search for non-sender roles; the sender is resolved via get_agent_me
    search_fragments = {frag.lower(): role for role, frag in CASCADE_AGENTS if role != SENDER_ROLE}
    exclude_lower = exclude_handle.lower() if exclude_handle else None

    page = 1
    while True:
        response = await client.agent_api_peers.list_agent_peers(
            page=page,
            page_size=100,
            request_options=DEFAULT_REQUEST_OPTIONS,
        )

        if not response.data:
            break

        for peer in response.data:
            peer_handle = getattr(peer, "handle", None) or ""
            # Skip the sender (already known via get_agent_me)
            if exclude_lower and exclude_lower in peer_handle.lower():
                continue
            handle_lower = peer_handle.lower()
            for fragment, role in search_fragments.items():
                if role in found:
                    continue
                if fragment in handle_lower:
                    found[role] = {
                        "id": peer.id,
                        "name": peer.name,
                        "handle": peer_handle,
                    }
                    break

        # Stop early if we found all non-sender agents
        if len(found) == len(search_fragments):
            break

        total_pages = (
            getattr(response.metadata, "total_pages", None) or 1 if response.metadata else 1
        )
        if page >= total_pages:
            break
        page += 1

    return found


async def trigger_pipeline(
    regulation_text: str,
    target_handle: str | None = None,
) -> str:
    """Create a Band chat room, add all 5 cascade agents, and send the regulation.

    The regulation is @mentioned to the Monitor only — the cascade flows
    automatically from there (Monitor → Legal Parser → Impact Mapper →
    Gap Analyst → Planner) because each agent resolves the next via
    get_participants() in core/cascade.py.

    Args:
        regulation_text: The regulation content to send to the Monitor.
        target_handle: Optional full handle of the Monitor agent
            (e.g. "@username/regiq-monitor"). If None, peers are searched
            by the "regiq-monitor" substring.

    Returns:
        The created chat room ID.

    Raises:
        RuntimeError: If any REST API call fails.
        ValueError: If the Monitor peer cannot be found (other missing
            agents are warned but non-fatal — the cascade will degrade
            gracefully with fallback slugs).
    """
    sender_id, sender_key = get_agent_credentials(SENDER_AGENT_NAME)
    rest_url = get_band_rest_url().rstrip("/")

    log_info(f"Band client: auth as '{SENDER_AGENT_NAME}', REST URL: {rest_url}")
    client = AsyncRestClient(api_key=sender_key, base_url=rest_url)

    room_id: str | None = None
    try:
        # Step 1: Resolve sender's own identity via GET /agent/me
        log_info("Band client: resolving sender identity via /agent/me...")
        self_identity = await _get_self_identity(client)
        log_info(
            f"Band client: sender is {self_identity['name']} "
            f"(id={self_identity['id']}, handle={self_identity['handle']})"
        )

        # Step 2: Find the other 4 cascade agents via peer search
        log_info("Band client: searching peers for other cascade agents...")
        peers = await _find_cascade_peers(client, exclude_handle=self_identity["handle"])

        # If target_handle was provided, override the monitor match
        if target_handle:
            monitor_peer = None
            target_lower = target_handle.lower()
            page = 1
            while True:
                response = await client.agent_api_peers.list_agent_peers(
                    page=page,
                    page_size=100,
                    request_options=DEFAULT_REQUEST_OPTIONS,
                )
                if not response.data:
                    break
                for peer in response.data:
                    peer_handle = getattr(peer, "handle", None) or ""
                    if target_lower in peer_handle.lower():
                        monitor_peer = {
                            "id": peer.id,
                            "name": peer.name,
                            "handle": peer_handle,
                        }
                        break
                if monitor_peer:
                    break
                total_pages = (
                    getattr(response.metadata, "total_pages", None) or 1 if response.metadata else 1
                )
                if page >= total_pages:
                    break
                page += 1
            if monitor_peer:
                peers[ENTRY_AGENT_ROLE] = monitor_peer

        # Combine self + peers for the full 5/5
        all_agents: dict[str, dict[str, str]] = {
            **peers,
            SENDER_ROLE: self_identity,
        }

        # The Monitor is required — it's the cascade entry point
        monitor_peer = all_agents.get(ENTRY_AGENT_ROLE)
        if not monitor_peer:
            raise ValueError(
                "Could not find Monitor agent peer (searched for 'regiq-monitor' in handles). "
                "Ensure the Monitor agent is registered and visible to the sender agent."
            )

        found_roles = list(all_agents.keys())
        missing_roles = [role for role, _ in CASCADE_AGENTS if role not in all_agents]
        log_info(
            f"Band client: found {len(found_roles)}/{len(CASCADE_AGENTS)} cascade agents: "
            f"{', '.join(found_roles)}"
        )
        if missing_roles:
            log_warning(
                f"Band client: missing agents: {', '.join(missing_roles)} — "
                "cascade may fail when these agents are needed. "
                "Add them as contacts or ensure they are visible peers."
            )

        for role, peer in all_agents.items():
            log_info(
                f"Band client:   {role} → {peer['name']} (id={peer['id']}, handle={peer['handle']})"
            )

        # Step 3: Create a chat room
        log_info("Band client: creating chat room...")
        chat_response = await client.agent_api_chats.create_agent_chat(
            chat=ChatRoomRequest(),
            request_options=DEFAULT_REQUEST_OPTIONS,
        )
        room_id = chat_response.data.id
        log_success(f"Band client: created room {room_id}")

        # Step 4: Add cascade agents as participants.
        # Skip the sender — it's auto-added as the room creator, so adding
        # it again returns 409 Conflict. It's still a full participant:
        # get_participants() sees it, and it can be @mentioned (the Planner
        # uses this to self-mention when posting the final report).
        for role, peer in all_agents.items():
            if role == SENDER_ROLE:
                log_info(
                    f"Band client: {role} is the room creator — already a participant, skipping add"
                )
                continue
            log_info(f"Band client: adding {role} ({peer['name']}) to room...")
            await client.agent_api_participants.add_agent_chat_participant(
                chat_id=room_id,
                participant=ParticipantRequest(participant_id=peer["id"]),
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
            log_success(f"Band client: {role} added as participant")

        # Step 5: Send the regulation message mentioning ONLY the Monitor
        # (the cascade entry point). Subsequent @mentions are handled by
        # each agent's on_message via core/cascade.py.
        log_info("Band client: sending regulation message to Monitor...")
        mention = ChatMessageRequestMentionsItem(
            id=monitor_peer["id"],
            handle=monitor_peer["handle"],
        )
        message_request = ChatMessageRequest(
            content=regulation_text,
            mentions=[mention],
        )
        await client.agent_api_messages.create_agent_chat_message(
            chat_id=room_id,
            message=message_request,
            request_options=DEFAULT_REQUEST_OPTIONS,
        )
        log_success(
            f"Band client: regulation sent to room {room_id}, cascade triggered "
            f"(Monitor @mentioned, {len(all_agents)} agents in room)"
        )

        return room_id

    except Exception as e:
        log_error(f"Band client: trigger failed: {e}")
        if room_id:
            log_error(f"Band client: orphan room {room_id} may need manual cleanup")
        raise
    finally:
        await client._client_wrapper.httpx_client.httpx_client.aclose()
