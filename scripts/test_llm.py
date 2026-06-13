from core.llm import get_balanced_llm, get_fast_llm, get_embeddings
from utils.loggers import log_info, log_success, log_error


def main():
    log_info("Testing AI/ML API connection...")

    llm = get_fast_llm()
    log_info("Sending chat request to gemini-2.5-flash...")
    try:
        response = llm.invoke("Say hello in one sentence.")
        log_success(f"Chat response: {response.content}")
    except Exception as e:
        log_error(f"Chat request failed: {e}")
        return


    log_info("Sending chat request to sonnet 4.6...")
    try:
        llm = get_balanced_llm()
        response = llm.invoke("Say hello in a cool way in one sentence.")
        log_success(f"Chat response: {response.content}")
    except Exception as e:
        log_error(f"Chat request failed: {e}")
        return


    embeddings = get_embeddings()
    log_info("Sending embeddings request to text-embedding-3-small...")
    try:
        vector = embeddings.embed_query("test query")
        log_success(f"Embeddings OK — vector dim={len(vector)}")
    except Exception as e:
        log_error(f"Embeddings request failed: {e}")
        return

    log_success("All AI/ML API checks passed!")


if __name__ == "__main__":
    main()
