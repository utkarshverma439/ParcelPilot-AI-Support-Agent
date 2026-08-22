DOCUMENT_METADATA = {
    "01_Support_Policy_v3_CURRENT.pdf": {
        "document_name": "Support Policy v3",
        "document_type": "support_policy",
        "version": "v3",
        "status": "CURRENT",
        "effective_date": "2026-05-01",
        "customer_account_id": None,
        "source_priority": 80,
        "section": "support_policy",
    },
    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "document_name": "Support Policy v2",
        "document_type": "support_policy",
        "version": "v2",
        "status": "DEPRECATED",
        "effective_date": "2025-01-01",
        "customer_account_id": None,
        "source_priority": 20,
        "section": "support_policy",
    },
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "document_name": "Cancellation & Service Credit SOP v4",
        "document_type": "sop",
        "version": "v4",
        "status": "CURRENT",
        "effective_date": "2026-06-15",
        "customer_account_id": None,
        "source_priority": 75,
        "section": "cancellation_sop",
    },
    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "document_name": "Product Operations Guide",
        "document_type": "product_docs",
        "version": "current",
        "status": "CURRENT",
        "effective_date": "2026-08-14",
        "customer_account_id": None,
        "source_priority": 70,
        "section": "product_ops",
    },
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "document_name": "Northstar Logistics Enterprise Agreement",
        "document_type": "customer_agreement",
        "version": "current",
        "status": "ACTIVE",
        "effective_date": "2026-01-01",
        "customer_account_id": "ACCT-001",
        "source_priority": 90,
        "section": "enterprise_agreement",
    },
    "06_LumenWorks_Service_Agreement.pdf": {
        "document_name": "LumenWorks Service Agreement",
        "document_type": "customer_agreement",
        "version": "current",
        "status": "ACTIVE",
        "effective_date": "2026-03-01",
        "customer_account_id": "ACCT-002",
        "source_priority": 85,
        "section": "service_agreement",
    },
}

ACCOUNT_TO_DOCUMENT = {
    "ACCT-001": "05_Northstar_Logistics_Enterprise_Agreement.pdf",
    "ACCT-002": "06_LumenWorks_Service_Agreement.pdf",
}


def get_authority_priority(metadata: dict) -> int:
    return metadata.get("source_priority", 50)


def rank_sources(sources: list[dict]) -> list[dict]:
    return sorted(sources, key=lambda s: get_authority_priority(s.get("metadata", {})), reverse=True)


def filter_deprecated(sources: list[dict]) -> list[dict]:
    return [s for s in sources if s.get("metadata", {}).get("status") != "DEPRECATED"]


def get_customer_agreement_priority(account_id: str) -> int:
    if account_id in ("ACCT-001", "ACCT-002"):
        return 90
    return 0


def detect_conflicts(sources: list[dict]) -> list[dict]:
    conflicts = []
    by_type = {}
    for s in sources:
        doc_type = s.get("metadata", {}).get("document_type", "unknown")
        by_type.setdefault(doc_type, []).append(s)

    for doc_type, items in by_type.items():
        if len(items) > 1:
            priorities = [get_authority_priority(i.get("metadata", {})) for i in items]
            if max(priorities) - min(priorities) > 30:
                conflicts.append({
                    "document_type": doc_type,
                    "sources": [i.get("metadata", {}).get("document_name", "unknown") for i in items],
                    "resolution": "Use highest priority source",
                })
    return conflicts
