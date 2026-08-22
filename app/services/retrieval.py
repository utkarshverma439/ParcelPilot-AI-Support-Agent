from app.vector.store import VectorStore
from app.services.reliability import (
    rank_sources,
    filter_deprecated,
    detect_conflicts,
    get_authority_priority,
    ACCOUNT_TO_DOCUMENT,
)
from typing import Optional


class RetrievalService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def search_documents(
        self,
        query: str,
        account_id: Optional[str] = None,
        include_deprecated: bool = False,
        n_results: int = 10,
    ) -> dict:
        raw_results = self.vector_store.search(
            query=query,
            n_results=n_results * 2,
            where=None,
        )

        if account_id:
            raw_results = [
                r for r in raw_results
                if r.get("metadata", {}).get("customer_account_id", "") in ("", account_id)
            ]

        if not include_deprecated:
            raw_results = filter_deprecated(raw_results)

        ranked = rank_sources(raw_results)[:n_results]

        conflicts = detect_conflicts(ranked)

        citations = []
        for r in ranked:
            meta = r.get("metadata", {})
            citations.append({
                "document": meta.get("document_name", "unknown"),
                "page": meta.get("page_number", 0),
                "section": meta.get("section", "general"),
                "source_type": meta.get("document_type", "unknown"),
                "authority": meta.get("source_priority", 50),
                "status": meta.get("status", "unknown"),
                "excerpt": r.get("text", "")[:300],
            })

        return {
            "results": ranked,
            "citations": citations,
            "conflicts": conflicts,
            "query": query,
            "account_id": account_id,
        }
