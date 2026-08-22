from app.services.retrieval import RetrievalService
from app.security.auth import UserContext, is_internal
from typing import Optional


def search_documents_tool(
    retrieval: RetrievalService,
    user: UserContext,
    query: str,
    account_id: Optional[str] = None,
) -> dict:
    effective_account = account_id

    if not is_internal(user):
        effective_account = user.account_id
    elif not account_id:
        effective_account = None

    result = retrieval.search_documents(
        query=query,
        account_id=effective_account,
        include_deprecated=is_internal(user),
    )

    return {
        "tool": "search_documents",
        "query": query,
        "account_id": effective_account,
        "citations": result["citations"],
        "conflicts": result["conflicts"],
        "result_count": len(result["citations"]),
    }
