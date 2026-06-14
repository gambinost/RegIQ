from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from core.llm import get_embeddings
from core.settings import get_settings
from utils.loggers import log_info, log_warning

_vectorstore: QdrantVectorStore | None = None


def _get_vectorstore() -> QdrantVectorStore:
    global _vectorstore
    if _vectorstore is None:
        settings = get_settings()
        client = QdrantClient(
            url=settings.QDRANT_CLUSTER_ENDPOINT,
            api_key=settings.QDRANT_API_KEY,
        )
        _vectorstore = QdrantVectorStore(
            client=client,
            collection_name=settings.QDRANT_COLLECTION,
            embedding=get_embeddings(),
        )
    return _vectorstore


async def query_knowledge_base(query: str, top_k: int = 5) -> str:
    try:
        vectorstore = _get_vectorstore()
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": top_k,
                "score_threshold": 0.5,
            },
        )
        docs: list[Document] = await retriever.ainvoke(query)

        if not docs:
            log_info("RAG: No documents retrieved")
            return ""

        log_info(f"RAG: Retrieved {len(docs)} chunks")
        parts = []
        for doc in docs:
            source = doc.metadata.get("source", "unknown")
            parts.append(f"---\nSource: {source}\n{doc.page_content}\n---")
        return "\n\n".join(parts)

    except Exception as e:
        log_warning(f"RAG retrieval failed: {e}")
        return ""
