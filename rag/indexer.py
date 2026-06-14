from dotenv import load_dotenv

load_dotenv()

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import Distance

from core.llm import get_embeddings
from core.settings import get_settings
from utils.loggers import log_info, log_success, log_error

KB_DIR = Path(__file__).resolve().parent.parent / "data" / "company_kb"


def seed_knowledge_base() -> int:
    settings = get_settings()
    embeddings = get_embeddings()

    md_files = sorted(KB_DIR.glob("*.md"))
    if not md_files:
        log_error(f"No .md files found in {KB_DIR}")
        return 0

    log_info(f"Found {len(md_files)} documents in {KB_DIR}")

    all_chunks: list[str] = []
    all_metadatas: list[dict] = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n", " "],
    )

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        if not text.strip():
            log_error(f"Empty file: {md_file.name}")
            continue

        docs = splitter.create_documents(
            texts=[text],
            metadatas=[{"source": md_file.name}],
        )
        for doc in docs:
            all_chunks.append(doc.page_content)
            all_metadatas.append(doc.metadata)

        log_info(f"  {md_file.name}: {len(docs)} chunks")

    if not all_chunks:
        log_error("No chunks generated from documents")
        return 0

    log_info(f"Total: {len(all_chunks)} chunks. Seeding into Qdrant...")

    QdrantVectorStore.from_texts(
        texts=all_chunks,
        embedding=embeddings,
        metadatas=all_metadatas,
        url=settings.QDRANT_CLUSTER_ENDPOINT,
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION,
        distance=Distance.COSINE,
        force_recreate=True,
        batch_size=16,
        grpc_port=6334,
        prefer_grpc=True,
        timeout=120,
    )

    log_success(
        f"Seeded {len(all_chunks)} chunks from {len(md_files)} files into '{settings.QDRANT_COLLECTION}'"
    )
    return len(all_chunks)


if __name__ == "__main__":
    count = seed_knowledge_base()
    print(f"\nDone. {count} chunks seeded.")
