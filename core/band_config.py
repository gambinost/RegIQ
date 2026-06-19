import os
from pathlib import Path

import yaml

from core.settings import get_settings
from utils.loggers import log_info

AGENTS_CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "agent_config.yaml"

# Map of agent names to their env var prefixes
AGENT_ENV_MAP = {
    "monitor": "BAND_MONITOR",
    "legal_parser": "BAND_LEGAL_PARSER",
    "impact_mapper": "BAND_IMPACT_MAPPER",
    "gap_analyst": "BAND_GAP_ANALYST",
    "remediation_planner": "BAND_REMEDIATION_PLANNER",
}


def _ensure_config_exists() -> None:
    """Generate agent_config.yaml from env vars if it doesn't exist."""
    if AGENTS_CONFIG_PATH.exists():
        return

    config = {}
    for agent_name, env_prefix in AGENT_ENV_MAP.items():
        agent_id = os.getenv(f"{env_prefix}_AGENT_ID", "")
        api_key = os.getenv(f"{env_prefix}_API_KEY", "")
        if agent_id and api_key:
            config[agent_name] = {"agent_id": agent_id, "api_key": api_key}

    if config:
        AGENTS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AGENTS_CONFIG_PATH, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        log_info(f"Generated {AGENTS_CONFIG_PATH} from environment variables")
    else:
        log_info("No BAND_* env vars found, using existing config")


def get_agent_credentials(name: str) -> tuple[str, str]:
    """Load agent credentials from config file (generated from env vars if needed)."""
    _ensure_config_exists()
    log_info(f"Loading credentials for agent: {name}")

    from band.config.loader import load_agent_config

    agent_id, api_key = load_agent_config(name, config_path=str(AGENTS_CONFIG_PATH))
    return agent_id, api_key


def get_band_ws_url() -> str:
    return get_settings().THENVOI_WS_URL


def get_band_rest_url() -> str:
    return get_settings().THENVOI_REST_URL
