from pathlib import Path

from band.config.loader import load_agent_config

from core.settings import get_settings
from utils.loggers import log_info

AGENTS_CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "agent_config.yaml"


def get_agent_credentials(name: str) -> tuple[str, str]:
    log_info(f"Loading credentials for agent: {name}")
    agent_id, api_key = load_agent_config(name, config_path=str(AGENTS_CONFIG_PATH))
    return agent_id, api_key


def get_band_ws_url() -> str:
    return get_settings().THENVOI_WS_URL


def get_band_rest_url() -> str:
    return get_settings().THENVOI_REST_URL
