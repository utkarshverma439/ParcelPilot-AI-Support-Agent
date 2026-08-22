import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.security.auth import (
    get_user,
    is_internal,
    can_access_account,
    can_access_order,
    can_access_ticket,
    UserRole,
    UserContext,
)


def test_northstar_user_scoped_to_own_account():
    user = get_user("customer_northstar")
    assert user is not None
    assert user.account_id == "ACCT-001"
    assert can_access_account(user, "ACCT-001") is True
    assert can_access_account(user, "ACCT-002") is False


def test_lumenworks_user_scoped_to_own_account():
    user = get_user("customer_lumenworks")
    assert user is not None
    assert user.account_id == "ACCT-002"
    assert can_access_account(user, "ACCT-002") is True
    assert can_access_account(user, "ACCT-001") is False


def test_internal_users_can_access_all_accounts():
    for uid in ("support_agent", "operations_admin"):
        user = get_user(uid)
        assert user is not None
        assert is_internal(user) is True
        assert can_access_account(user, "ACCT-001") is True
        assert can_access_account(user, "ACCT-002") is True
        assert can_access_account(user, "ACCT-003") is True


def test_customer_cannot_access_other_account_orders():
    user = get_user("customer_northstar")
    assert can_access_order(user, "ACCT-001") is True
    assert can_access_order(user, "ACCT-002") is False


def test_internal_can_access_all_orders():
    user = get_user("support_agent")
    assert can_access_order(user, "ACCT-001") is True
    assert can_access_order(user, "ACCT-004") is True


def test_customer_cannot_access_other_account_tickets():
    user = get_user("customer_lumenworks")
    assert can_access_ticket(user, "ACCT-002") is True
    assert can_access_ticket(user, "ACCT-001") is False


def test_nonexistent_user():
    user = get_user("nonexistent_user")
    assert user is None


def test_customer_role_is_not_internal():
    user = get_user("customer_northstar")
    assert is_internal(user) is False


def test_support_agent_role_is_internal():
    user = get_user("support_agent")
    assert is_internal(user) is True
    assert user.role == UserRole.SUPPORT_AGENT


def test_operations_admin_role_is_internal():
    user = get_user("operations_admin")
    assert is_internal(user) is True
    assert user.role == UserRole.OPERATIONS_ADMIN
