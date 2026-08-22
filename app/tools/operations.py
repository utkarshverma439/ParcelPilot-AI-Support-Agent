from app.data.repository import Repository
from app.security.auth import UserContext, can_access_account, can_access_order, can_access_ticket
from typing import Optional


def get_account_tool(repo: Repository, user: UserContext, account_id: str) -> dict:
    if not can_access_account(user, account_id):
        return {"tool": "get_account", "error": "Access denied: cannot access this account"}

    account = repo.get_account(account_id)
    if not account:
        return {"tool": "get_account", "error": f"Account {account_id} not found"}

    return {
        "tool": "get_account",
        "account": {
            "account_id": account.account_id,
            "account_name": account.account_name,
            "plan": account.plan,
            "status": account.status,
            "csm": account.csm,
            "premium_support": account.premium_support,
            "contract_file": account.contract_file,
            "notes": account.notes,
        },
    }


def get_order_tool(repo: Repository, user: UserContext, order_id: str) -> dict:
    order = repo.get_order(order_id)
    if not order:
        return {"tool": "get_order", "error": f"Order {order_id} not found"}

    if not can_access_order(user, order.account_id):
        return {"tool": "get_order", "error": "Access denied: cannot access this order"}

    return {
        "tool": "get_order",
        "order": {
            "order_id": order.order_id,
            "account_id": order.account_id,
            "carrier": order.carrier,
            "status": order.status,
            "booked_at": order.booked_at,
            "pickup_window_start": order.pickup_window_start,
            "pickup_window_end": order.pickup_window_end,
            "pickup_actual_at": order.pickup_actual_at,
            "shipment_fee_inr": order.shipment_fee_inr,
            "carrier_fault": order.carrier_fault,
            "customer_fault": order.customer_fault,
            "cancellation_requested_at": order.cancellation_requested_at,
            "notes": order.notes,
        },
    }


def get_ticket_tool(repo: Repository, user: UserContext, ticket_id: str) -> dict:
    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        return {"tool": "get_ticket", "error": f"Ticket {ticket_id} not found"}

    if not can_access_ticket(user, ticket.account_id):
        return {"tool": "get_ticket", "error": "Access denied: cannot access this ticket"}

    return {
        "tool": "get_ticket",
        "ticket": {
            "ticket_id": ticket.ticket_id,
            "account_id": ticket.account_id,
            "created_at": ticket.created_at,
            "status": ticket.status,
            "subject": ticket.subject,
            "description": ticket.description,
            "channel": ticket.channel,
            "assigned_to": ticket.assigned_to,
            "last_customer_message_at": ticket.last_customer_message_at,
            "historical_resolution": ticket.historical_resolution,
        },
    }


def get_sla_status_tool(repo: Repository, user: UserContext, ticket_id: str) -> dict:
    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        return {"tool": "get_sla_status", "error": f"Ticket {ticket_id} not found"}

    if not can_access_ticket(user, ticket.account_id):
        return {"tool": "get_sla_status", "error": "Access denied"}

    account = repo.get_account(ticket.account_id)
    if not account:
        return {"tool": "get_sla_status", "error": "Account not found"}

    return {
        "tool": "get_sla_status",
        "ticket_id": ticket_id,
        "account_id": ticket.account_id,
        "plan": account.plan,
        "status": ticket.status,
        "created_at": ticket.created_at,
        "subject": ticket.subject,
    }


def get_orders_by_account_tool(repo: Repository, user: UserContext, account_id: str) -> dict:
    if not can_access_account(user, account_id):
        return {"tool": "get_orders_by_account", "error": "Access denied"}

    orders = repo.get_orders_by_account(account_id)
    return {
        "tool": "get_orders_by_account",
        "account_id": account_id,
        "orders": [
            {
                "order_id": o.order_id,
                "carrier": o.carrier,
                "status": o.status,
                "booked_at": o.booked_at,
                "shipment_fee_inr": o.shipment_fee_inr,
                "carrier_fault": o.carrier_fault,
                "cancellation_requested_at": o.cancellation_requested_at,
                "notes": o.notes,
            }
            for o in orders
        ],
    }


def get_tickets_by_account_tool(repo: Repository, user: UserContext, account_id: str) -> dict:
    if not can_access_account(user, account_id):
        return {"tool": "get_tickets_by_account", "error": "Access denied"}

    tickets = repo.get_tickets_by_account(account_id)
    return {
        "tool": "get_tickets_by_account",
        "account_id": account_id,
        "tickets": [
            {
                "ticket_id": t.ticket_id,
                "status": t.status,
                "subject": t.subject,
                "created_at": t.created_at,
                "assigned_to": t.assigned_to,
                "historical_resolution": t.historical_resolution,
            }
            for t in tickets
        ],
    }
