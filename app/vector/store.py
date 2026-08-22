import chromadb
from typing import Optional
from app.config import get_settings


class VectorStore:
    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(path="./data/processed/chromadb")
        self.collection = self.client.get_or_create_collection(
            name="parcelpilot_docs",
            metadata={"hnsw:space": "cosine"},
        )

    def _clean_metadata(self, meta: dict) -> dict:
        cleaned = {}
        for k, v in meta.items():
            if v is None:
                cleaned[k] = ""
            elif isinstance(v, (str, int, float, bool)):
                cleaned[k] = v
            else:
                cleaned[k] = str(v)
        return cleaned

    def add_documents(self, chunks: list[dict]):
        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [self._clean_metadata(c["metadata"]) for c in chunks]

        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i : i + batch_size],
                documents=texts[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

    def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> list[dict]:
        count = self.collection.count()
        if count == 0:
            return []

        kwargs = {
            "query_texts": [query],
            "n_results": min(n_results, count),
        }
        if where:
            kwargs["where"] = where
        if where_document:
            kwargs["where_document"] = where_document

        results = self.collection.query(**kwargs)

        output = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                output.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "id": results["ids"][0][i] if results["ids"] else "",
                })
        return output
