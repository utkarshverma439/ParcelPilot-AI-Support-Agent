import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.data.models import init_db
from app.data.ingestion import run_ingestion
from app.vector.store import VectorStore


def main():
    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    print(f"Embedding model: {settings.embedding_model}")
    print()

    SessionLocal = init_db(settings.database_url)
    db = SessionLocal()

    vector_store = VectorStore()

    try:
        run_ingestion(db, vector_store)
        print("\nIngestion complete!")
    except Exception as e:
        print(f"\nError during ingestion: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
