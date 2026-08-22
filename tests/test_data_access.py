import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.data.repository import Repository
from app.data.models import Account, Order, Ticket, Base
from app.security.auth import get_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.merge(Account(
        account_id="ACCT-001", account_name="Northstar Logistics",
        plan="Enterprise", status="active", csm="Priya Mehta",
        premium_support=True, contract_file="05_Northstar.pdf",
    ))
    session.merge(Account(
        account_id="ACCT-002", account_name="LumenWorks",
        plan="Growth", status="active", csm="Arjun Rao",
        premium_support=False, contract_file="06_LumenWorks.pdf",
    ))
    session.merge(Order(
        order_id="ORD-1001", account_id="ACCT-001", carrier="SwiftShip",
        status="BOOKED", booked_at="2026-08-16 09:00", shipment_fee_inr=4200.0,
        carrier_fault=False, customer_fault=False, notes="Test order",
    ))
    session.merge(Order(
        order_id="ORD-2001", account_id="ACCT-002", carrier="SwiftShip",
        status="BOOKED", booked_at="2026-08-16 09:00", shipment_fee_inr=1800.0,
        carrier_fault=False, customer_fault=False, notes="Test order 2",
    ))
    session.merge(Ticket(
        ticket_id="TKT-501", account_id="ACCT-001", created_at="2026-08-16 10:30",
        status="open", subject="All shipment creation is failing",
        channel="email", assigned_to="Rohit",
    ))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def repo(db_session):
    return Repository(db_session)


def test_customer_can_get_own_account(repo):
    user = get_user("customer_northstar")
    account = repo.get_account("ACCT-001", user.account_id)
    assert account is not None
    assert account.account_name == "Northstar Logistics"


def test_customer_cannot_get_other_account(repo):
    user = get_user("customer_northstar")
    account = repo.get_account("ACCT-002", user.account_id)
    assert account is None


def test_internal_can_get_any_account(repo):
    user = get_user("support_agent")
    account = repo.get_account("ACCT-002", user.account_id)
    assert account is not None


def test_customer_can_get_own_order(repo):
    user = get_user("customer_northstar")
    order = repo.get_order("ORD-1001", user.account_id)
    assert order is not None


def test_customer_cannot_get_other_order(repo):
    user = get_user("customer_northstar")
    order = repo.get_order("ORD-2001", user.account_id)
    assert order is None


def test_customer_can_get_own_ticket(repo):
    user = get_user("customer_northstar")
    ticket = repo.get_ticket("TKT-501", user.account_id)
    assert ticket is not None


def test_customer_cannot_get_other_ticket(repo):
    user = get_user("customer_northstar")
    ticket = repo.get_ticket("TKT-502", user.account_id)
    assert ticket is None


def test_get_orders_by_account_scoped(repo):
    user = get_user("customer_northstar")
    orders = repo.get_orders_by_account("ACCT-001", user.account_id)
    assert len(orders) >= 1
    assert all(o.account_id == "ACCT-001" for o in orders)


def test_get_orders_by_account_denied(repo):
    user = get_user("customer_northstar")
    orders = repo.get_orders_by_account("ACCT-002", user.account_id)
    assert len(orders) == 0
