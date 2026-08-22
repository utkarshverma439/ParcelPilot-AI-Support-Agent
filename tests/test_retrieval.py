import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.services.retrieval import RetrievalService
from app.services.reliability import DOCUMENT_METADATA


class MockVectorStore:
    def __init__(self):
        self.documents = []

    def add_documents(self, chunks):
        self.documents.extend(chunks)

    def search(self, query, n_results=10, where=None, where_document=None):
        results = []
        for doc in self.documents:
            score = 0.5
            if "cancel" in query.lower() and "cancel" in doc.get("text", "").lower():
                score = 0.9
            elif "credit" in query.lower() and "credit" in doc.get("text", "").lower():
                score = 0.8
            elif "sla" in query.lower() and "sla" in doc.get("text", "").lower():
                score = 0.85

            meta = doc.get("metadata", {})
            if where and where.get("$or"):
                customer_match = False
                for condition in where["$or"]:
                    if condition.get("customer_account_id") is None:
                        customer_match = True
                        break
                    if condition.get("customer_account_id") == meta.get("customer_account_id"):
                        customer_match = True
                        break
                if not customer_match:
                    continue

            results.append({
                "text": doc.get("text", ""),
                "metadata": meta,
                "distance": 1.0 - score,
                "id": doc.get("id", ""),
            })

        results.sort(key=lambda x: x.get("distance", 1.0))
        return results[:n_results]


@pytest.fixture
def mock_retrieval():
    vs = MockVectorStore()
    for filename, meta in DOCUMENT_METADATA.items():
        vs.add_documents([{
            "id": f"{filename}:p1:c0",
            "text": f"Sample text about {meta.get('document_type', 'general')} from {meta.get('document_name', 'unknown')}",
            "metadata": {
                "document_name": meta.get("document_name", "unknown"),
                "document_type": meta.get("document_type", "unknown"),
                "version": meta.get("version", "unknown"),
                "status": meta.get("status", "unknown"),
                "source_priority": meta.get("source_priority", 50),
                "page_number": 1,
                "customer_account_id": meta.get("customer_account_id"),
                "section": meta.get("section", "general"),
            },
        }])
    return RetrievalService(vs)


def test_retrieval_filters_by_account(mock_retrieval):
    result = mock_retrieval.search_documents("cancellation", account_id="ACCT-001")
    citations = result["citations"]
    for c in citations:
        assert c["authority"] >= 50 or c["source_type"] != "customer_agreement"


def test_retrieval_excludes_deprecated_by_default(mock_retrieval):
    result = mock_retrieval.search_documents("support policy")
    citations = result["citations"]
    deprecated = [c for c in citations if c["status"] == "DEPRECATED"]
    assert len(deprecated) == 0


def test_retrieval_returns_citations(mock_retrieval):
    result = mock_retrieval.search_documents("cancellation fee")
    assert "citations" in result
    assert isinstance(result["citations"], list)


def test_retrieval_detects_conflicts(mock_retrieval):
    result = mock_retrieval.search_documents("support policy")
    assert "conflicts" in result
    assert isinstance(result["conflicts"], list)
