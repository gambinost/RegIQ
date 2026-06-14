from dotenv import load_dotenv

load_dotenv()

from rag.indexer import seed_knowledge_base

if __name__ == "__main__":
    try:
        count = seed_knowledge_base()
        if count == 0:
            print("\nFailed: No chunks were seeded.")
            raise SystemExit(1)
        print(f"\nDone. {count} chunks seeded into Qdrant.")
    except Exception as e:
        print(f"\nError: {e}")
        raise SystemExit(1)
