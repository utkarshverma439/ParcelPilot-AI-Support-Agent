import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.tools.actions import confirm_action_tool, create_escalation_tool
from app.data.models import Action, Ticket, init_db, Base
from app.data.repository import Repository
from app.security.auth import get_user, UserContext, UserRole
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.merge(Ticket(
        ticket_id="TKT-501", account_id="ACCT-001", created_at="2026-08-16 10:30",
        status="open", subject="Test ticket", channel="email", assigned_to="Rohit",
    ))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def repo(db_session):
    return Repository(db_session)


def test_escalation_requires_confirmation(repo):
    user = get_user("support_agent")
    result = create_escalation_tool(repo, user, "TKT-501", reason="Test escalation")
    assert result["status"] == "pending"
    assert result["confirmation_required"] is True
    assert "want me to" in result["message"].lower() or "confirm" in result["message"].lower()


def test_confirm_action_executes(repo):
    user = get_user("support_agent")
    create_result = create_escalation_tool(repo, user, "TKT-501", reason="Test")
    action_id = create_result["action_id"]

    confirm_result = confirm_action_tool(repo, action_id)
    assert confirm_result["status"] == "executed"


def test_duplicate_confirm_is_idempotent(repo):
    user = get_user("support_agent")
    create_result = create_escalation_tool(repo, user, "TKT-501", reason="Test")
    action_id = create_result["action_id"]

    confirm_action_tool(repo, action_id)
    second_confirm = confirm_action_tool(repo, action_id)
    assert "error" in second_confirm
    assert "already executed" in second_confirm["error"]


def test_customer_cannot_create_escalation(repo):
    user = get_user("customer_northstar")
    result = create_escalation_tool(repo, user, "TKT-501", reason="Test")
    assert "error" in result
    assert "internal" in result["error"].lower()


def test_confirm_nonexistent_action(repo):
    result = confirm_action_tool(repo, "ACT-NONEXISTENT")
    assert "error" in result
    assert "not found" in result["error"]
