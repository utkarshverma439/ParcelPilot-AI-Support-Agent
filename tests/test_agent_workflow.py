import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.agent.graph import extract_account_id, extract_order_id, extract_ticket_id


def test_extract_northstar_account():
    assert extract_account_id("Can Northstar cancel ORD-1001?") == "ACCT-001"


def test_extract_lumenworks_account():
    assert extract_account_id("Show me LumenWorks orders") == "ACCT-002"


def test_extract_beacon_account():
    assert extract_account_id("What about Beacon Retail?") == "ACCT-003"


def test_extract_axis_labs_account():
    assert extract_account_id("Axis Labs has an issue") == "ACCT-004"


def test_extract_account_id_none_when_not_found():
    assert extract_account_id("What is the weather today?") is None


def test_extract_order_id():
    assert extract_order_id("Can Northstar cancel ORD-1001?") == "ORD-1001"


def test_extract_order_id_none():
    assert extract_order_id("Show me orders") is None


def test_extract_ticket_id():
    assert extract_ticket_id("What is the status of TKT-501?") == "TKT-501"


def test_extract_ticket_id_none():
    assert extract_ticket_id("Show me tickets") is None


def test_extract_multiple_entities():
    query = "Can Northstar cancel ORD-1001? They also have TKT-501 open."
    assert extract_account_id(query) == "ACCT-001"
    assert extract_order_id(query) == "ORD-1001"
    assert extract_ticket_id(query) == "TKT-501"
