import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.services.reliability import (
    DOCUMENT_METADATA,
    get_authority_priority,
    rank_sources,
    filter_deprecated,
    detect_conflicts,
)


def test_current_policy_higher_than_deprecated():
    current = DOCUMENT_METADATA["01_Support_Policy_v3_CURRENT.pdf"]
    deprecated = DOCUMENT_METADATA["02_Support_Policy_v2_DEPRECATED.pdf"]
    assert current["source_priority"] > deprecated["source_priority"]


def test_customer_agreement_highest_priority():
    northstar = DOCUMENT_METADATA["05_Northstar_Logistics_Enterprise_Agreement.pdf"]
    current_policy = DOCUMENT_METADATA["01_Support_Policy_v3_CURRENT.pdf"]
    assert northstar["source_priority"] > current_policy["source_priority"]


def test_lumenworks_agreement_highest_for_their_account():
    lumenworks = DOCUMENT_METADATA["06_LumenWorks_Service_Agreement.pdf"]
    current_policy = DOCUMENT_METADATA["01_Support_Policy_v3_CURRENT.pdf"]
    assert lumenworks["source_priority"] > current_policy["source_priority"]


def test_deprecated_policy_lowest_among_policies():
    deprecated = DOCUMENT_METADATA["02_Support_Policy_v2_DEPRECATED.pdf"]
    sop = DOCUMENT_METADATA["03_Cancellation_and_Service_Credit_SOP_v4.pdf"]
    product = DOCUMENT_METADATA["04_Product_Operations_Guide_and_Known_Issues.pdf"]
    assert deprecated["source_priority"] < sop["source_priority"]
    assert deprecated["source_priority"] < product["source_priority"]


def test_rank_sources_orders_by_priority():
    sources = [
        {"metadata": {"source_priority": 20, "document_name": "Deprecated"}},
        {"metadata": {"source_priority": 90, "document_name": "Northstar Agreement"}},
        {"metadata": {"source_priority": 80, "document_name": "Policy v3"}},
    ]
    ranked = rank_sources(sources)
    assert ranked[0]["metadata"]["document_name"] == "Northstar Agreement"
    assert ranked[1]["metadata"]["document_name"] == "Policy v3"
    assert ranked[2]["metadata"]["document_name"] == "Deprecated"


def test_filter_deprecated_removes_deprecated():
    sources = [
        {"metadata": {"status": "CURRENT", "document_name": "Policy v3"}},
        {"metadata": {"status": "DEPRECATED", "document_name": "Policy v2"}},
        {"metadata": {"status": "ACTIVE", "document_name": "Northstar"}},
    ]
    filtered = filter_deprecated(sources)
    assert len(filtered) == 2
    assert all(s["metadata"]["status"] != "DEPRECATED" for s in filtered)


def test_detect_conflicts_finds_priority_gaps():
    sources = [
        {"metadata": {"document_type": "support_policy", "source_priority": 80, "document_name": "Policy v3"}},
        {"metadata": {"document_type": "support_policy", "source_priority": 20, "document_name": "Policy v2"}},
    ]
    conflicts = detect_conflicts(sources)
    assert len(conflicts) == 1
    assert conflicts[0]["document_type"] == "support_policy"


def test_no_conflict_when_single_source():
    sources = [
        {"metadata": {"document_type": "sop", "source_priority": 75, "document_name": "SOP v4"}},
    ]
    conflicts = detect_conflicts(sources)
    assert len(conflicts) == 0


def test_customer_scope_on_agreements():
    northstar = DOCUMENT_METADATA["05_Northstar_Logistics_Enterprise_Agreement.pdf"]
    lumenworks = DOCUMENT_METADATA["06_LumenWorks_Service_Agreement.pdf"]
    assert northstar["customer_account_id"] == "ACCT-001"
    assert lumenworks["customer_account_id"] == "ACCT-002"
    assert northstar["customer_account_id"] != lumenworks["customer_account_id"]
