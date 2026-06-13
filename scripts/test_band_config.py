from core.band_config import get_agent_credentials, get_band_ws_url, get_band_rest_url
from utils.loggers import log_info, log_success, log_error


def main():
    log_info("Testing Band config loading...")

    for agent_name in ["monitor", "legal_parser"]:
        try:
            agent_id, api_key = get_agent_credentials(agent_name)
            log_success(f"{agent_name}: agent_id={agent_id[:8]}... api_key={api_key[:12]}...")
        except Exception as e:
            log_error(f"Failed to load {agent_name}: {e}")
            return

    ws_url = get_band_ws_url()
    rest_url = get_band_rest_url()
    log_info(f"Band WS URL:   {ws_url}")
    log_info(f"Band REST URL: {rest_url}")

    log_success("All Band config checks passed!")


if __name__ == "__main__":
    main()
