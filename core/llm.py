from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.settings import get_settings
from utils.loggers import log_info


def get_fast_llm() -> ChatOpenAI:
    s = get_settings()
    log_info(f"Initializing fast LLM: {s.MODEL_FAST}")
    return ChatOpenAI(
        model=s.MODEL_FAST,
        api_key=s.AIML_API_KEY,
        base_url=s.OPENAI_BASE_URL,
        temperature=0,
    )


def get_balanced_llm() -> ChatOpenAI:
    s = get_settings()
    log_info(f"Initializing balanced LLM: {s.MODEL_BALANCED}")
    return ChatOpenAI(
        model=s.MODEL_BALANCED,
        api_key=s.AIML_API_KEY,
        base_url=s.OPENAI_BASE_URL,
        temperature=0,
    )


def get_embeddings() -> OpenAIEmbeddings:
    s = get_settings()
    log_info(f"Initializing embeddings: {s.MODEL_EMBEDDINGS}")
    return OpenAIEmbeddings(
        model=s.MODEL_EMBEDDINGS,
        api_key=s.AIML_API_KEY,
        base_url=s.OPENAI_BASE_URL,
        check_embedding_ctx_length=False,
    )
