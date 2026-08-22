import uuid
import json
from datetime import datetime
from app.data.repository import Repository
from app.data.models import Action
from app.security.auth import UserContext, is_internal
from typing import Optional


def create_escalation_tool(
    repo: Repository,
    user: UserContext,
    ticket_id: str,
    reason: str,
    priority: str = "high",
    team: str = "Support",
) -> dict:
    if not is_internal(user):
        return {"tool": "create_escalation", "error": "Only internal users can create escalations"}

    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        return {"tool": "create_escalation", "error": f"Ticket {ticket_id} not found"}

    action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "ticket_id": ticket_id,
        "reason": reason,
        "priority": priority,
        "team": team,
        "account_id": ticket.account_id,
    }

    action = Action(
        action_id=action_id,
        action_type="create_escalation",
        status="pending",
        requested_by=user.user_id,
        account_id=ticket.account_id,
        payload_json=json.dumps(payload),
        created_at=datetime.utcnow().isoformat(),
    )
    repo.create_action(action)

    return {
        "tool": "create_escalation",
        "action_id": action_id,
        "status": "pending",
        "details": {
            "ticket_id": ticket_id,
            "reason": reason,
            "priority": priority,
            "team": team,
            "account_id": ticket.account_id,
        },
        "confirmation_required": True,
        "message": f"I can create the following escalation:\n\nTicket: {ticket_id}\nReason: {reason}\nPriority: {priority}\nTeam: {team}\n\nDo you want me to create this escalation?",
    }


def update_ticket_tool(
    repo: Repository,
    user: UserContext,
    ticket_id: str,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    if not is_internal(user):
        return {"tool": "update_ticket", "error": "Only internal users can update tickets"}

    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        return {"tool": "update_ticket", "error": f"Ticket {ticket_id} not found"}

    action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "ticket_id": ticket_id,
        "status": status,
        "assigned_to": assigned_to,
        "notes": notes,
    }

    action = Action(
        action_id=action_id,
        action_type="update_ticket",
        status="pending",
        requested_by=user.user_id,
        account_id=ticket.account_id,
        payload_json=json.dumps(payload),
        created_at=datetime.utcnow().isoformat(),
    )
    repo.create_action(action)

    changes = []
    if status:
        changes.append(f"Status → {status}")
    if assigned_to:
        changes.append(f"Assigned to → {assigned_to}")
    if notes:
        changes.append(f"Notes → {notes}")

    return {
        "tool": "update_ticket",
        "action_id": action_id,
        "status": "pending",
        "details": payload,
        "confirmation_required": True,
        "message": f"I can update ticket {ticket_id}:\n\n" + "\n".join(changes) + "\n\nDo you want me to apply these changes?",
    }


def create_followup_task_tool(
    repo: Repository,
    user: UserContext,
    ticket_id: str,
    task_description: str,
    assignee: str,
) -> dict:
    if not is_internal(user):
        return {"tool": "create_followup_task", "error": "Only internal users can create tasks"}

    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        return {"tool": "create_followup_task", "error": f"Ticket {ticket_id} not found"}

    action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "ticket_id": ticket_id,
        "task_description": task_description,
        "assignee": assignee,
    }

    action = Action(
        action_id=action_id,
        action_type="create_followup_task",
        status="pending",
        requested_by=user.user_id,
        account_id=ticket.account_id,
        payload_json=json.dumps(payload),
        created_at=datetime.utcnow().isoformat(),
    )
    repo.create_action(action)

    return {
        "tool": "create_followup_task",
        "action_id": action_id,
        "status": "pending",
        "details": payload,
        "confirmation_required": True,
        "message": f"I can create a follow-up task:\n\nTicket: {ticket_id}\nTask: {task_description}\nAssignee: {assignee}\n\nDo you want me to create this task?",
    }


def confirm_action_tool(repo: Repository, action_id: str) -> dict:
    action = repo.get_action(action_id)
    if not action:
        return {"tool": "confirm_action", "error": f"Action {action_id} not found"}

    if action.status == "executed":
        return {"tool": "confirm_action", "error": "Action already executed (idempotent)"}

    if action.status != "pending" and action.status != "confirmed":
        return {"tool": "confirm_action", "error": f"Action cannot be confirmed in status: {action.status}"}

    confirmed = repo.confirm_action(action_id)
    if not confirmed:
        return {"tool": "confirm_action", "error": "Confirmation failed"}

    executed = repo.execute_action(action_id)
    if not executed:
        return {"tool": "confirm_action", "error": "Execution failed"}

    return {
        "tool": "confirm_action",
        "action_id": action_id,
        "status": "executed",
        "message": f"Action {action_id} has been executed successfully.",
    }
