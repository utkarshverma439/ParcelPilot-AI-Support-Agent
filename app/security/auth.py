from dataclasses import dataclass
from typing import Optional
from enum import Enum


class UserRole(Enum):
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    OPERATIONS_ADMIN = "operations_admin"


@dataclass
class UserContext:
    user_id: str
    role: UserRole
    account_id: Optional[str] = None


MOCK_USERS = {
    "customer_northstar": UserContext(
        user_id="customer_northstar",
        role=UserRole.CUSTOMER,
        account_id="ACCT-001",
    ),
    "customer_lumenworks": UserContext(
        user_id="customer_lumenworks",
        role=UserRole.CUSTOMER,
        account_id="ACCT-002",
    ),
    "support_agent": UserContext(
        user_id="support_agent",
        role=UserRole.SUPPORT_AGENT,
        account_id=None,
    ),
    "operations_admin": UserContext(
        user_id="operations_admin",
        role=UserRole.OPERATIONS_ADMIN,
        account_id=None,
    ),
}


def get_user(user_id: str) -> Optional[UserContext]:
    return MOCK_USERS.get(user_id)


def is_internal(user: UserContext) -> bool:
    return user.role in (UserRole.SUPPORT_AGENT, UserRole.OPERATIONS_ADMIN)


def can_access_account(user: UserContext, account_id: str) -> bool:
    if is_internal(user):
        return True
    return user.account_id == account_id


def can_access_order(user: UserContext, order_account_id: str) -> bool:
    return can_access_account(user, order_account_id)


def can_access_ticket(user: UserContext, ticket_account_id: str) -> bool:
    return can_access_account(user, ticket_account_id)
