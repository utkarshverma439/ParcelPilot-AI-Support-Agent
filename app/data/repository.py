from sqlalchemy.orm import Session
from app.data.models import Account, Order, Ticket, Action, AuditLog
from typing import Optional


class Repository:
    def __init__(self, db: Session):
        self.db = db

    def get_account(self, account_id: str, user_account_id: Optional[str] = None) -> Optional[Account]:
        if user_account_id and user_account_id != account_id:
            return None
        return self.db.query(Account).filter(Account.account_id == account_id).first()

    def get_all_accounts(self) -> list[Account]:
        return self.db.query(Account).all()

    def get_order(self, order_id: str, user_account_id: Optional[str] = None) -> Optional[Order]:
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if order and user_account_id and order.account_id != user_account_id:
            return None
        return order

    def get_orders_by_account(self, account_id: str, user_account_id: Optional[str] = None) -> list[Order]:
        if user_account_id and user_account_id != account_id:
            return []
        return self.db.query(Order).filter(Order.account_id == account_id).all()

    def get_ticket(self, ticket_id: str, user_account_id: Optional[str] = None) -> Optional[Ticket]:
        ticket = self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if ticket and user_account_id and ticket.account_id != user_account_id:
            return None
        return ticket

    def get_tickets_by_account(self, account_id: str, user_account_id: Optional[str] = None) -> list[Ticket]:
        if user_account_id and user_account_id != account_id:
            return []
        return self.db.query(Ticket).filter(Ticket.account_id == account_id).all()

    def get_all_tickets(self) -> list[Ticket]:
        return self.db.query(Ticket).all()

    def get_all_orders(self) -> list[Order]:
        return self.db.query(Order).all()

    def get_open_tickets(self) -> list[Ticket]:
        return self.db.query(Ticket).filter(Ticket.status == "open").all()

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

    def create_action(self, action: Action) -> Action:
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def get_action(self, action_id: str) -> Optional[Action]:
        return self.db.query(Action).filter(Action.action_id == action_id).first()

    def confirm_action(self, action_id: str) -> Optional[Action]:
        from datetime import datetime
        action = self.get_action(action_id)
        if not action or action.status != "pending":
            return None
        action.status = "confirmed"
        action.confirmed_at = datetime.utcnow().isoformat()
        self.db.commit()
        self.db.refresh(action)
        return action

    def execute_action(self, action_id: str) -> Optional[Action]:
        from datetime import datetime
        action = self.get_action(action_id)
        if not action or action.status != "confirmed":
            return None
        action.status = "executed"
        action.executed_at = datetime.utcnow().isoformat()
        self.db.commit()
        self.db.refresh(action)
        return action

    def get_pending_actions_for_account(self, account_id: str) -> list[Action]:
        return self.db.query(Action).filter(
            Action.account_id == account_id,
            Action.status.in_(["pending", "confirmed"])
        ).all()

    def log_audit(self, audit: AuditLog) -> AuditLog:
        self.db.add(audit)
        self.db.commit()
        return audit

    def find_order_by_context(self, order_id: str) -> Optional[Order]:
        return self.db.query(Order).filter(Order.order_id == order_id).first()

    def find_ticket_by_context(self, ticket_id: str) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
